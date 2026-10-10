"""FastAPI backend for the Campus Customs dashboard.

Start from the backend/ folder:
    uvicorn main:app --reload --port 8000

- Read routes (tickets, cash, approvals) go through the MCP server, the same
  way the agents see shop data.
- Approving or rejecting a payment and resetting the database are human-only
  actions. They live here, not in the MCP server, so no agent can call them.
  Approving is the only place cash moves.
"""

import asyncio
import importlib.util
import json
import shutil
import sqlite3
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:  # so `uvicorn main:app` from backend/ can import the backend package
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastmcp import Client  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from backend import agents, config  # noqa: E402

ORIGINAL_DB = ROOT / "data" / "campus_customs.db"
WORKING_DB = ROOT / "data" / "campus_customs_new.db"


def load_mcp_server():
    """Import mcp_server/server.py so routes can call its tools in-process."""
    spec = importlib.util.spec_from_file_location("campus_customs_mcp", config.MCP_SERVER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mcp_server = load_mcp_server()

app = FastAPI(title="Campus Customs API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

# Only one agent run at a time, so two runs can't both pass the same cash check.
agent_lock = asyncio.Lock()
runs: dict[int, dict] = {}  # ticket_id -> latest run state


async def mcp_call(tool: str, args: dict | None = None) -> dict:
    async with Client(mcp_server.mcp) as client:
        result = await client.call_tool(tool, args or {})
        return result.data


# ----------------------------------------------------------------- tickets


@app.get("/api/tickets")
async def list_tickets():
    """All tickets with their status (open or resolved) and any agent run state."""
    tickets = []
    for status in ("open", "resolved"):
        tickets += (await mcp_call("list_tickets", {"status": status}))["tickets"]
    tickets.sort(key=lambda t: t["id"])
    for t in tickets:
        t["run"] = runs.get(t["id"])
    return {"tickets": tickets}


@app.get("/api/tickets/{ticket_id}")
async def get_ticket(ticket_id: int):
    ticket = await mcp_call("get_ticket", {"ticket_id": ticket_id})
    if not ticket.get("found"):
        raise HTTPException(404, ticket.get("error"))
    return {**ticket, "run": runs.get(ticket_id)}


async def _run_team(ticket_id: int) -> None:
    try:
        decision = await agents.work_ticket(ticket_id)
        runs[ticket_id].update(
            state="done" if decision else "failed",
            decision=decision.model_dump() if decision else None,
        )
    except Exception as e:  # surfaced to the dashboard; details are in the audit trail
        runs[ticket_id].update(state="failed", error=f"{type(e).__name__}: {e}")
    finally:
        runs[ticket_id]["finished_at"] = now()
        agent_lock.release()


@app.post("/api/tickets/{ticket_id}/run", status_code=202)
async def run_ticket(ticket_id: int):
    """Start the agent team on one ticket in the background. Poll /api/events and this ticket for progress."""
    ticket = await mcp_call("get_ticket", {"ticket_id": ticket_id})
    if not ticket.get("found"):
        raise HTTPException(404, ticket.get("error"))
    if ticket["status"] == "resolved":
        raise HTTPException(409, f"Ticket {ticket_id} is already resolved.")
    if agent_lock.locked():
        busy = next((tid for tid, r in runs.items() if r["state"] == "running"), None)
        raise HTTPException(409, f"The agents are already working on ticket {busy}. Try again when it finishes.")
    await agent_lock.acquire()
    runs[ticket_id] = {"state": "running", "started_at": now(), "finished_at": None, "decision": None}
    asyncio.create_task(_run_team(ticket_id))
    return {"ticket_id": ticket_id, **runs[ticket_id]}


@app.get("/api/tickets/{ticket_id}/run")
async def run_status(ticket_id: int):
    """State of the latest agent run on this ticket (running / done / failed) and the Boss's decision."""
    if ticket_id not in runs:
        raise HTTPException(404, f"No agent run for ticket {ticket_id} since the server started.")
    return {"ticket_id": ticket_id, **runs[ticket_id]}


# ------------------------------------------------------------------ events


@app.get("/api/events")
async def events(limit: int = 50, after: int | None = None, ticket_id: int | None = None):
    """Recent agent events from output/audit_trail.json, oldest first.

    Each event has an `index`; pass `after=<last index>` to get only newer events.
    """
    path = config.AUDIT_TRAIL
    entries = json.loads(path.read_text()) if path.exists() and path.stat().st_size else []
    items = [{"index": i, **e} for i, e in enumerate(entries)]
    if ticket_id is not None:
        items = [e for e in items if e.get("ticket_id") == ticket_id]
    if after is not None:
        items = [e for e in items if e["index"] > after]
    limit = max(1, min(limit, 500))
    return {"total": len(entries), "events": items[-limit:]}


# ---------------------------------------------------------------- approvals


@app.get("/api/approvals")
async def pending_approvals():
    """Payments and purchase orders the agents prepared, waiting for a human."""
    return await mcp_call("list_pending_approvals")


class Decision(BaseModel):
    approved_by: str = "human"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(WORKING_DB, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


def add_month(iso_day: str) -> str:
    d = date.fromisoformat(iso_day)
    year, month = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
    for day in (d.day, 30, 29, 28):  # clamp e.g. Jan 31 -> Feb 28
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            continue
    raise ValueError(iso_day)


@app.post("/api/approvals/{request_id}/approve")
async def approve(request_id: int, body: Decision):
    """A human approves a prepared payment or purchase order. This is the only place cash moves.

    In one transaction: check the request is still waiting, refuse if the account
    can't cover it, subtract the cash, record the payment, mark an invoice paid
    (or move rent's next due date a month on), and mark the request approved.
    """
    conn = connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        req = conn.execute("SELECT * FROM approval_queue WHERE id = ?", (request_id,)).fetchone()
        if req is None:
            raise HTTPException(404, f"No approval request {request_id}.")
        if req["status"] != mcp_server.PENDING:
            raise HTTPException(409, f"Request {request_id} is already {req['status']}.")
        acct = conn.execute("SELECT balance FROM cash_accounts WHERE name = ?", (req["account"],)).fetchone()
        if acct is None:
            raise HTTPException(409, f"No cash account {req['account']!r}.")
        if req["amount"] > acct["balance"]:
            raise HTTPException(
                409,
                f"Refused: not enough cash. {req['account']} has ${acct['balance']:,.2f} and this needs ${req['amount']:,.2f}.",
            )

        today = conn.execute("SELECT date_today FROM desk").fetchone()["date_today"]
        new_balance = acct["balance"] - req["amount"]
        conn.execute("UPDATE cash_accounts SET balance = ?, date = ? WHERE name = ?", (new_balance, today, req["account"]))

        if req["kind"] == "payment" and req["ref_type"] == "invoice":
            kind, ref_id = "invoice", req["ref_id"]
            conn.execute("UPDATE invoices SET status = 'paid' WHERE id = ?", (ref_id,))
        elif req["kind"] == "payment" and req["ref_type"] == "lease":
            kind, ref_id = "rent", req["ref_id"]
            due = conn.execute("SELECT next_due FROM leases WHERE id = ?", (ref_id,)).fetchone()["next_due"]
            conn.execute("UPDATE leases SET next_due = ? WHERE id = ?", (add_month(due), ref_id))
        else:  # purchase order; stock arrives after the vendor's lead time, so inventory isn't changed here
            kind, ref_id = "purchase_order", req["id"]

        cur = conn.execute(
            "INSERT INTO payments (kind, ref_id, amount, account, paid_at, approved_by) VALUES (?, ?, ?, ?, ?, ?)",
            (kind, ref_id, req["amount"], req["account"], today, body.approved_by),
        )
        conn.execute("UPDATE approval_queue SET status = 'approved' WHERE id = ?", (request_id,))
        conn.execute("COMMIT")
        return {
            "ok": True,
            "request_id": request_id,
            "payment_id": cur.lastrowid,
            "kind": kind,
            "ref_id": ref_id,
            "amount": req["amount"],
            "account": req["account"],
            "balance_after": new_balance,
            "approved_by": body.approved_by,
        }
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


@app.post("/api/approvals/{request_id}/reject")
async def reject(request_id: int, body: Decision):
    """A human rejects a prepared payment or purchase order. No cash moves."""
    conn = connect()
    try:
        req = conn.execute("SELECT status FROM approval_queue WHERE id = ?", (request_id,)).fetchone()
        if req is None:
            raise HTTPException(404, f"No approval request {request_id}.")
        if req["status"] != mcp_server.PENDING:
            raise HTTPException(409, f"Request {request_id} is already {req['status']}.")
        conn.execute("UPDATE approval_queue SET status = 'rejected' WHERE id = ?", (request_id,))
        return {"ok": True, "request_id": request_id, "status": "rejected", "rejected_by": body.approved_by}
    finally:
        conn.close()


# --------------------------------------------------------------------- cash


@app.get("/api/cash")
async def cash():
    """Current checking balance from cash_accounts, plus what's waiting for approval."""
    return await mcp_call("get_cash_balance", {"account": "checking"})


# -------------------------------------------------------------------- reset


@app.post("/api/reset")
async def reset():
    """Copy data/campus_customs.db over data/campus_customs_new.db for a fresh run.

    The audit trail is kept (it's append-only).
    """
    if agent_lock.locked():
        raise HTTPException(409, "Can't reset while the agents are running.")
    shutil.copyfile(ORIGINAL_DB, WORKING_DB)
    mcp_server.ensure_schema()  # re-add approval_queue and message_drafts
    runs.clear()
    return {"ok": True, "reset_at": now(), "database": "data/campus_customs_new.db"}


@app.get("/api/health")
async def health():
    return {"ok": True, "model": config.MODEL_NAME, "agent_running": agent_lock.locked()}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
