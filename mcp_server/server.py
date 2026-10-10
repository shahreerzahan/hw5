"""Campus Customs MCP server.

The only way the agent team touches shop data. Every tool works on the
working copy data/campus_customs_new.db and only returns what is stored
there; if a record is missing, the tool says so instead of guessing.

Write tools never move money or contact anyone:
- prepare_payment / prepare_purchase_order queue a request in approval_queue
  with status "waiting_for_approval" (a human approves it later).
- save_customer_draft stores a draft in message_drafts (never sent).
- resolve_ticket marks a ticket resolved with a resolution note.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from fastmcp import FastMCP

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "campus_customs_new.db"

mcp = FastMCP("campus-customs")

# Tables this server adds to the working copy. They are not in the original
# database, so they are created on startup (and again after a reset).
SCHEMA = """
CREATE TABLE IF NOT EXISTS approval_queue (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL,            -- 'payment' or 'purchase_order'
    ticket_id INTEGER,
    ref_type TEXT,                 -- payment: 'invoice' or 'lease'
    ref_id INTEGER,
    vendor_id INTEGER,
    sku TEXT,
    size TEXT,
    qty INTEGER,
    amount REAL NOT NULL,
    account TEXT NOT NULL,
    reason TEXT NOT NULL,
    requested_by TEXT NOT NULL,
    status TEXT NOT NULL,          -- 'waiting_for_approval', later 'approved'/'rejected'
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS message_drafts (
    id INTEGER PRIMARY KEY,
    ticket_id INTEGER NOT NULL,
    recipient TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    drafted_by TEXT NOT NULL,
    status TEXT NOT NULL,          -- always 'draft'; nothing is ever sent
    created_at TEXT NOT NULL
);
"""

PENDING = "waiting_for_approval"


def connect(readonly: bool = True) -> sqlite3.Connection:
    mode = "ro" if readonly else "rw"
    conn = sqlite3.connect(f"file:{DB_PATH}?mode={mode}", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def query(sql: str, params: tuple = ()) -> list[dict]:
    """Run a read-only query and return rows as dicts."""
    conn = connect()
    try:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def execute(sql: str, params: tuple = ()) -> int:
    """Run one write statement in its own transaction; return lastrowid."""
    conn = connect(readonly=False)
    try:
        with conn:
            return conn.execute(sql, params).lastrowid
    finally:
        conn.close()


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_schema() -> None:
    conn = connect(readonly=False)
    try:
        conn.executescript(SCHEMA)
    finally:
        conn.close()


def cash_position(account: str) -> dict | None:
    """Balance, amount already queued for approval, and what is left."""
    rows = query("SELECT name, balance, date FROM cash_accounts WHERE name = ?", (account,))
    if not rows:
        return None
    pending = query(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM approval_queue WHERE account = ? AND status = ?",
        (account, PENDING),
    )[0]["total"]
    acct = rows[0]
    return {
        "account": acct["name"],
        "balance": acct["balance"],
        "as_of": acct["date"],
        "pending_approval_total": pending,
        "available_after_pending": acct["balance"] - pending,
    }


# ---------------------------------------------------------------- read tools


@mcp.tool
def get_desk_date() -> dict:
    """Get the shop's "today" (desk.date_today) and desk notes.

    Reads the desk table. Use this date, not the real clock, for every
    overdue or days-until-due check.
    """
    rows = query("SELECT date_today, notes FROM desk")
    if not rows:
        return {"found": False, "error": "The desk table is empty."}
    return {"found": True, **rows[0]}


@mcp.tool
def list_tickets(status: str = "open") -> dict:
    """List tickets with a given status ("open" or "resolved"), oldest first.

    Reads the tickets table.
    """
    rows = query(
        "SELECT id, type, requester, subject, status, created_at FROM tickets WHERE status = ? ORDER BY created_at",
        (status,),
    )
    return {"status": status, "count": len(rows), "tickets": rows}


@mcp.tool
def get_ticket(ticket_id: int) -> dict:
    """Get one ticket with all its fields (type, requester, sku/size/qty, lease_id, invoice_id, notes).

    Reads the tickets table.
    """
    rows = query("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    if not rows:
        return {"found": False, "error": f"No ticket with id={ticket_id}."}
    return {"found": True, **rows[0]}


@mcp.tool
def check_stock(sku: str, size: str) -> dict:
    """Check stock on hand for a SKU in a given size, with its unit cost and list price.

    Reads the inventory and pricing tables. Use for customer orders and bulk
    or discount requests (e.g. sku "CC-TEE-WHITE" size "S").
    """
    rows = query(
        """
        SELECT i.sku, i.name, i.size, i.qty AS qty_in_stock, i.location,
               p.unit_cost, p.list_price
        FROM inventory i
        LEFT JOIN pricing p ON p.sku = i.sku
        WHERE i.sku = ? AND i.size = ?
        """,
        (sku, size),
    )
    if not rows:
        sizes = [r["size"] for r in query("SELECT size FROM inventory WHERE sku = ?", (sku,))]
        return {
            "found": False,
            "error": f"No inventory row for sku={sku!r}, size={size!r}.",
            "sizes_available_for_sku": sizes,
        }
    return {"found": True, **rows[0]}


@mcp.tool
def list_vendors() -> dict:
    """List every vendor with its specialty and lead time in days.

    Reads the vendors table. Use to find who can restock an item and how long it takes.
    """
    rows = query("SELECT id, name, specialty, lead_days FROM vendors ORDER BY id")
    return {"count": len(rows), "vendors": rows}


@mcp.tool
def get_vendor_invoices(vendor_id: int) -> dict:
    """Get a vendor's details and lead time, plus any open (unpaid) invoices owed to them.

    Reads the vendors and invoices tables. Use to see whether an unpaid bill
    is holding up a vendor's work, such as a reprint.
    """
    vendors = query(
        "SELECT id, name, specialty, lead_days FROM vendors WHERE id = ?",
        (vendor_id,),
    )
    if not vendors:
        return {"found": False, "error": f"No vendor with id={vendor_id}."}
    open_invoices = query(
        """
        SELECT id, amount, due_date, status, description
        FROM invoices
        WHERE vendor_id = ? AND status = 'open'
        ORDER BY due_date
        """,
        (vendor_id,),
    )
    return {
        "found": True,
        "vendor": vendors[0],
        "open_invoices": open_invoices,
        "open_invoice_total": sum(inv["amount"] for inv in open_invoices),
    }


@mcp.tool
def get_invoice(invoice_id: int) -> dict:
    """Get one invoice with its vendor's name and lead time.

    Reads the invoices and vendors tables.
    """
    rows = query(
        """
        SELECT inv.id, inv.vendor_id, v.name AS vendor_name, v.lead_days,
               inv.amount, inv.due_date, inv.status, inv.description
        FROM invoices inv
        LEFT JOIN vendors v ON v.id = inv.vendor_id
        WHERE inv.id = ?
        """,
        (invoice_id,),
    )
    if not rows:
        return {"found": False, "error": f"No invoice with id={invoice_id}."}
    return {"found": True, **rows[0]}


@mcp.tool
def get_lease(lease_id: int) -> dict:
    """Get a lease's space, landlord, monthly rent, and next due date.

    Reads the leases table. Use for rent notices.
    """
    rows = query(
        """
        SELECT id, space_name, landlord, monthly_rent, next_due, notes
        FROM leases
        WHERE id = ?
        """,
        (lease_id,),
    )
    if not rows:
        return {"found": False, "error": f"No lease with id={lease_id}."}
    return {"found": True, **rows[0]}


@mcp.tool
def get_cash_balance(account: str = "checking") -> dict:
    """Get a cash account's balance, the total already waiting for approval, and what is left after that.

    Reads the cash_accounts and approval_queue tables. "available_after_pending"
    is the most that can still be committed without going below zero.
    """
    pos = cash_position(account)
    if pos is None:
        names = [r["name"] for r in query("SELECT name FROM cash_accounts")]
        return {"found": False, "error": f"No cash account named {account!r}.", "accounts": names}
    return {"found": True, **pos}


@mcp.tool
def list_pending_approvals() -> dict:
    """List payments and purchase orders waiting for human approval.

    Reads the approval_queue table.
    """
    rows = query("SELECT * FROM approval_queue WHERE status = ? ORDER BY id", (PENDING,))
    return {"count": len(rows), "total": sum(r["amount"] for r in rows), "items": rows}


# --------------------------------------------------------------- write tools


@mcp.tool
def prepare_payment(
    ticket_id: int,
    ref_type: str,
    ref_id: int,
    amount: float,
    reason: str,
    requested_by: str,
    account: str = "checking",
) -> dict:
    """Queue a payment for human approval. No cash moves.

    ref_type is "invoice" (pays invoices.id) or "lease" (pays rent on leases.id).
    Refuses if the amount is more than the invoice amount or monthly rent, if
    the invoice is not open, or if it would take the account below zero after
    everything already waiting for approval. Writes to approval_queue.
    """
    if amount <= 0:
        return {"ok": False, "error": "Amount must be positive."}
    if ref_type == "invoice":
        inv = query("SELECT id, vendor_id, amount, status FROM invoices WHERE id = ?", (ref_id,))
        if not inv:
            return {"ok": False, "error": f"No invoice with id={ref_id}."}
        if inv[0]["status"] != "open":
            return {"ok": False, "error": f"Invoice {ref_id} is {inv[0]['status']!r}, not open."}
        limit, vendor_id = inv[0]["amount"], inv[0]["vendor_id"]
    elif ref_type == "lease":
        lease = query("SELECT id, monthly_rent FROM leases WHERE id = ?", (ref_id,))
        if not lease:
            return {"ok": False, "error": f"No lease with id={ref_id}."}
        limit, vendor_id = lease[0]["monthly_rent"], None
    else:
        return {"ok": False, "error": "ref_type must be 'invoice' or 'lease'."}
    if amount > limit:
        return {"ok": False, "error": f"Amount {amount} is more than the {ref_type} amount {limit}."}

    dup = query(
        "SELECT id FROM approval_queue WHERE kind = 'payment' AND ref_type = ? AND ref_id = ? AND status = ?",
        (ref_type, ref_id, PENDING),
    )
    if dup:
        return {"ok": False, "error": f"A payment for {ref_type} {ref_id} is already waiting for approval (request {dup[0]['id']})."}

    pos = cash_position(account)
    if pos is None:
        return {"ok": False, "error": f"No cash account named {account!r}."}
    if amount > pos["available_after_pending"]:
        return {
            "ok": False,
            "error": "Refused: not enough cash. This payment would take the account below zero.",
            "cash": pos,
            "amount_requested": amount,
        }

    request_id = execute(
        """
        INSERT INTO approval_queue
            (kind, ticket_id, ref_type, ref_id, vendor_id, amount, account, reason, requested_by, status, created_at)
        VALUES ('payment', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (ticket_id, ref_type, ref_id, vendor_id, amount, account, reason, requested_by, PENDING, now()),
    )
    return {
        "ok": True,
        "request_id": request_id,
        "status": PENDING,
        "note": "Queued for human approval. No cash has moved.",
        "cash_left_after_pending": pos["available_after_pending"] - amount,
    }


@mcp.tool
def prepare_purchase_order(
    ticket_id: int,
    vendor_id: int,
    sku: str,
    size: str,
    qty: int,
    reason: str,
    requested_by: str,
    account: str = "checking",
) -> dict:
    """Queue a restock purchase order for human approval. No cash moves.

    The amount is qty x pricing.unit_cost (never a guessed price). Refuses if
    the SKU/size or vendor doesn't exist, or if the order would take the
    account below zero after everything already waiting for approval. Flags
    vendors with open unpaid invoices, since they won't ship until paid.
    Writes to approval_queue.
    """
    if qty <= 0:
        return {"ok": False, "error": "qty must be positive."}
    item = query(
        """
        SELECT i.sku, i.size, p.unit_cost FROM inventory i
        LEFT JOIN pricing p ON p.sku = i.sku
        WHERE i.sku = ? AND i.size = ?
        """,
        (sku, size),
    )
    if not item:
        return {"ok": False, "error": f"No inventory row for sku={sku!r}, size={size!r}."}
    if item[0]["unit_cost"] is None:
        return {"ok": False, "error": f"No unit cost in pricing for {sku}."}
    vendor = query("SELECT id, name, lead_days FROM vendors WHERE id = ?", (vendor_id,))
    if not vendor:
        return {"ok": False, "error": f"No vendor with id={vendor_id}."}

    amount = qty * item[0]["unit_cost"]
    pos = cash_position(account)
    if pos is None:
        return {"ok": False, "error": f"No cash account named {account!r}."}
    if amount > pos["available_after_pending"]:
        return {
            "ok": False,
            "error": "Refused: not enough cash. This order would take the account below zero.",
            "cash": pos,
            "amount_requested": amount,
        }

    unpaid = query("SELECT id, amount, due_date FROM invoices WHERE vendor_id = ? AND status = 'open'", (vendor_id,))
    request_id = execute(
        """
        INSERT INTO approval_queue
            (kind, ticket_id, vendor_id, sku, size, qty, amount, account, reason, requested_by, status, created_at)
        VALUES ('purchase_order', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (ticket_id, vendor_id, sku, size, qty, amount, account, reason, requested_by, PENDING, now()),
    )
    result = {
        "ok": True,
        "request_id": request_id,
        "status": PENDING,
        "amount": amount,
        "vendor": vendor[0],
        "note": "Queued for human approval. No cash has moved and the vendor has not been contacted.",
        "cash_left_after_pending": pos["available_after_pending"] - amount,
    }
    if unpaid:
        result["warning"] = "Vendor has open unpaid invoices and won't ship until they are paid."
        result["open_invoices"] = unpaid
    return result


@mcp.tool
def save_customer_draft(ticket_id: int, recipient: str, subject: str, body: str, drafted_by: str) -> dict:
    """Save a customer message as a draft for a human to review. It is never sent.

    Writes to the message_drafts table.
    """
    if not query("SELECT id FROM tickets WHERE id = ?", (ticket_id,)):
        return {"ok": False, "error": f"No ticket with id={ticket_id}."}
    draft_id = execute(
        """
        INSERT INTO message_drafts (ticket_id, recipient, subject, body, drafted_by, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'draft', ?)
        """,
        (ticket_id, recipient, subject, body, drafted_by, now()),
    )
    return {"ok": True, "draft_id": draft_id, "status": "draft", "note": "Saved as a draft. Nothing was sent."}


@mcp.tool
def resolve_ticket(ticket_id: int, resolution: str) -> dict:
    """Mark a ticket resolved and append the resolution to its notes.

    Writes to the tickets table. Refuses if the ticket is already resolved.
    """
    rows = query("SELECT id, status, notes FROM tickets WHERE id = ?", (ticket_id,))
    if not rows:
        return {"ok": False, "error": f"No ticket with id={ticket_id}."}
    if rows[0]["status"] == "resolved":
        return {"ok": False, "error": f"Ticket {ticket_id} is already resolved."}
    notes = (rows[0]["notes"] or "").rstrip()
    notes = f"{notes}\nResolution: {resolution}".strip()
    execute("UPDATE tickets SET status = 'resolved', notes = ? WHERE id = ?", (notes, ticket_id))
    return {"ok": True, "ticket_id": ticket_id, "status": "resolved"}


ensure_schema()

if __name__ == "__main__":
    mcp.run(show_banner=False)
