# Campus Customs Agent Harness

Reference for the agent team: what is in the database and why each table matters.

- **Original (read-only):** `data/campus_customs.db`
- **Working copy (agents update this):** `data/campus_customs_new.db`

## Tables

### desk
Fields: `date_today` (TEXT), `notes` (TEXT)

Why it matters: Sets the shop's "today" (2026-08-31), so agents judge due dates and overdue items against this date instead of the real clock.

### tickets
Fields: `id` (INTEGER, PK), `type` (TEXT), `requester` (TEXT), `subject` (TEXT), `sku` (TEXT), `size` (TEXT), `qty` (INTEGER), `lease_id` (INTEGER, FK → leases.id), `invoice_id` (INTEGER, FK → invoices.id), `status` (TEXT), `notes` (TEXT), `created_at` (TEXT)

Why it matters: The agents' work queue. Each ticket's `type` decides which agent handles it, and its `sku`/`lease_id`/`invoice_id` point to the records the agent needs.

### inventory
Fields: `sku` (TEXT), `name` (TEXT), `size` (TEXT), `qty` (INTEGER), `location` (TEXT); PK (`sku`, `size`)

Why it matters: Stock on hand by SKU and size, so agents can tell whether an order can be filled now or needs a reprint.

### pricing
Fields: `sku` (TEXT, PK), `unit_cost` (REAL), `list_price` (REAL)

Why it matters: Cost and list price for each SKU, so agents can quote prices and check that a discount still leaves a margin.

### vendors
Fields: `id` (INTEGER, PK), `name` (TEXT), `specialty` (TEXT), `lead_days` (INTEGER)

Why it matters: Who can restock or deliver and how fast (`lead_days`), so agents can give realistic dates for out-of-stock items.

### leases
Fields: `id` (INTEGER, PK), `space_name` (TEXT), `landlord` (TEXT), `monthly_rent` (REAL), `next_due` (TEXT), `notes` (TEXT)

Why it matters: The shop's rent obligation: amount, landlord, and next due date for rent notices.

### cash_accounts
Fields: `name` (TEXT, PK), `balance` (REAL), `date` (TEXT)

Why it matters: How much cash is available, so agents check that a payment can be covered before approving it.

### payments
Fields: `id` (INTEGER, PK), `kind` (TEXT), `ref_id` (INTEGER), `amount` (REAL), `account` (TEXT), `paid_at` (TEXT), `approved_by` (TEXT)

Why it matters: Audit log of money going out (currently empty). Agents record every payment here with who approved it, linked back to a lease or invoice through `ref_id`.

### invoices
Fields: `id` (INTEGER, PK), `vendor_id` (INTEGER, FK → vendors.id), `amount` (REAL), `due_date` (TEXT), `status` (TEXT), `description` (TEXT)

Why it matters: Bills owed to vendors. Agents use them to see what is due or overdue and how much cash is already committed.

## Open tickets and their links

| Ticket | Type | Links to | What the linked data shows |
|---|---|---|---|
| 101 | customer_order | inventory, pricing (`CC-TEE-WHITE`, S); invoices 501 → vendors 1 | Size S has **0** in stock. Invoice 501 ($840 rush reprint from Bulldog Print Co, 5 lead days) is still **open** and was due 2026-08-28, so it is overdue. |
| 102 | rent_notice | leases 1; cash_accounts | Rent is $2,400, due 2026-09-02, and checking has $3,400. |
| 103 | price_override | inventory, pricing (`CC-HOOD-NAVY`, M) | They want 20 but only **8** are in stock. Cost is $22 and list price is $58. |

Ticket 101 is waiting on a reprint that hasn't been paid for. Paying both the rent ($2,400) and invoice 501 ($840) would use $3,240 of the $3,400 in checking.

## Agents

Built with PydanticAI in `backend/agents.py`. Prompts are in `backend/prompts/`, and data types are in `backend/models.py`. Every agent runs on **gpt-6-luna** through Portkey. All five agents share one MCP connection, and each one only sees the MCP tools its role needs. Every agent also has `ask_agent(agent, request)`, so any agent can ask any other for help (full connectivity).

| Agent | Prompt | Job | MCP tools | Tables it touches |
|---|---|---|---|---|
| Boss | `boss.md` | Reads the ticket, decides who works on it, checks the reports, makes the final call, resolves the ticket | get_desk_date, list_tickets, get_ticket, list_pending_approvals, resolve_ticket | desk, tickets, approval_queue |
| Inventory | `inventory.md` | Stock by SKU and size, shortfalls, which vendor can restock and how fast | get_desk_date, get_ticket, check_stock, list_vendors, get_vendor_invoices | desk, tickets, inventory, pricing, vendors, invoices |
| Accounting | `accounting.md` | Cash, invoices, margins. Queues payments and purchase orders for human approval | get_desk_date, get_ticket, get_cash_balance, list_pending_approvals, get_invoice, get_vendor_invoices, get_lease, check_stock, prepare_payment, prepare_purchase_order | desk, tickets, cash_accounts, invoices, vendors, leases, inventory, pricing, approval_queue |
| Facilities | `facilities.md` | Shop space: lease, landlord, rent amount and due date | get_desk_date, get_ticket, get_lease, get_cash_balance, list_pending_approvals | desk, tickets, leases, cash_accounts, approval_queue |
| Customer Service | `customer_service.md` | Drafts messages to customers (drafts only, never sent) | get_desk_date, get_ticket, check_stock, save_customer_draft | desk, tickets, inventory, pricing, message_drafts |

Output types: specialists return an `AgentReport`, and the Boss returns a `TicketDecision`.

Every agent-loop step is appended to `output/audit_trail.json`: time, run_id, ticket_id, agent, depth, step, tool, short args, short result, and stop reason (`tool_call`, `tool_error_retry`, `final_output`, `completed`, `usage_limit`, `error`, `guardrail`). The file is only ever appended to. If it isn't a valid JSON list, the code refuses to overwrite it.

## MCP tools

Server: `mcp_server/server.py` (FastMCP, name `campus-customs`). Every tool works on `data/campus_customs_new.db` and returns only stored values. If a record doesn't exist, the tool returns `found: false` (or `ok: false`) with an error message instead of guessing. The agents get all shop data through these tools; there is no other database layer.

The server adds two tables to the working copy on startup (they are not in the original database):
- **approval_queue**: payments and purchase orders `waiting_for_approval` (fields: id, kind, ticket_id, ref_type, ref_id, vendor_id, sku, size, qty, amount, account, reason, requested_by, status, created_at)
- **message_drafts**: customer message drafts, never sent (fields: id, ticket_id, recipient, subject, body, drafted_by, status, created_at)

### All tools

| Tool | Inputs | Tables | Read/Write | Used by |
|---|---|---|---|---|
| `get_desk_date` | none | desk | read | all agents |
| `list_tickets` | `status` | tickets | read | boss |
| `get_ticket` | `ticket_id` | tickets | read | all agents |
| `check_stock` | `sku`, `size` | inventory, pricing | read | inventory, accounting, customer_service |
| `list_vendors` | none | vendors | read | inventory |
| `get_vendor_invoices` | `vendor_id` | vendors, invoices | read | inventory, accounting |
| `get_invoice` | `invoice_id` | invoices, vendors | read | accounting |
| `get_lease` | `lease_id` | leases | read | facilities, accounting |
| `get_cash_balance` | `account` | cash_accounts, approval_queue | read | accounting, facilities |
| `list_pending_approvals` | none | approval_queue | read | boss, accounting, facilities |
| `prepare_payment` | `ticket_id`, `ref_type`, `ref_id`, `amount`, `reason`, `requested_by` | invoices / leases, cash_accounts → **approval_queue** | write (queue only) | accounting |
| `prepare_purchase_order` | `ticket_id`, `vendor_id`, `sku`, `size`, `qty`, `reason`, `requested_by` | inventory, pricing, vendors, invoices, cash_accounts → **approval_queue** | write (queue only) | accounting |
| `save_customer_draft` | `ticket_id`, `recipient`, `subject`, `body`, `drafted_by` | **message_drafts** | write (draft only) | customer_service |
| `resolve_ticket` | `ticket_id`, `resolution` | **tickets** | write | boss |

Which tickets the first three tools help:

| Tool | Helps ticket |
|---|---|
| `check_stock` | 101, 103 |
| `get_vendor_invoices` | 101 |
| `get_lease` | 102 |

### check_stock
- **Ticket 101:** It shows in one call that `CC-TEE-WHITE` size S has 0 in stock, so the agent knows the order can't be filled from the shelf.
- **Ticket 103:** It shows only 8 of the 20 `CC-HOOD-NAVY` size M hoodies are in stock, along with the $22 cost and $58 list price, so the agent can size the order and check any bulk discount against cost.

### get_vendor_invoices
- **Ticket 101:** It returns Bulldog Print Co's 5-day lead time and its open $840 invoice 501 (due 2026-08-28) for the size S reprint. This lets the agent see that the reprint bill is overdue and must be dealt with before a restock date can be promised.

### get_lease
- **Ticket 102:** It returns the landlord (Elm City Properties), the $2,400 rent, and the 2026-09-02 due date straight from lease 1, so the agent can check the rent notice against the actual lease terms.

## Safety

### Guardrails for real customers and real money
- **Humans approve all money.** Agents can only queue payments and purchase orders (`approval_queue`, status `waiting_for_approval`). No agent tool writes to `payments` or changes `cash_accounts`.
- **Cash can't go below zero.** `prepare_payment` and `prepare_purchase_order` refuse if the amount is more than the balance minus everything already waiting for approval.
- **No made-up amounts.** A payment can't exceed the invoice amount or monthly rent, the invoice must be open, and the same invoice or lease can't be queued twice. Purchase orders are priced from `pricing.unit_cost`, never from a number the model chose.
- **The vendor rule is surfaced.** Purchase orders to a vendor with open unpaid invoices come back with a warning, since that vendor won't ship until it is paid.
- **No real outreach.** Customer messages are saved to `message_drafts` with status `draft`. No tool sends email or contacts a vendor or the landlord.
- **Least privilege.** Each agent sees only its own MCP tools. Only Accounting can queue money, only Customer Service can save drafts, and only the Boss can resolve a ticket.
- **One source of truth.** All data comes through the MCP server over `campus_customs_new.db`. The original `campus_customs.db` is never written.
- **Shop date.** Overdue and due-date checks use `desk.date_today`, not the real clock.
- **Audit everything.** Every step is in the append-only `output/audit_trail.json`, so a human can trace who did what and why.

### Limits that keep token use down (`backend/config.py`)
| Limit | Value |
|---|---|
| Model | gpt-6-luna only, reasoning effort `low` |
| Max model requests (steps) per agent run | 10 |
| Max tool calls per agent run | 15 |
| Max total tokens per agent run | 80,000 |
| Max delegation depth | 2 (boss → specialist → specialist) |
| Max agent runs per ticket (boss + all delegations) | 8 |
| Delegation loops | refused: an agent can't ask itself or anyone already in the chain above it |
| Parallel tool calls | off (one step at a time) |
| Audit fields | cut to 300 characters |

When a limit is hit, the agent stops and the trail records `usage_limit` or `guardrail`. The calling agent then finishes with what it has instead of retrying.


## Backend routes

`backend/main.py` (FastAPI). Start it from `backend/` with `uvicorn main:app --reload --port 8000`. Read routes go through the MCP server. Approve, reject and reset are human-only and aren't MCP tools, so agents can't call them.

- `GET /api/tickets`: all tickets with their status (open or resolved) and the latest agent run state.
- `GET /api/tickets/{id}`: one ticket with every field and its run state.
- `POST /api/tickets/{id}/run`: starts the agent team on that ticket in the background (one run at a time; refuses resolved tickets).
- `GET /api/tickets/{id}/run`: state of that ticket's latest run (running, done or failed) and the Boss's final decision.
- `GET /api/events?limit=&after=&ticket_id=`: recent agent events from `output/audit_trail.json` (agent, tool, args, result or what it said, stop reason). Pass `after=<index>` to get only new events.
- `GET /api/approvals`: payments and purchase orders the agents prepared that are waiting for a human.
- `POST /api/approvals/{id}/approve`: a human approves; this is the only place cash moves. Subtracts `cash_accounts`, adds a `payments` row, marks the invoice paid (or moves rent's `next_due` a month on), and refuses if there isn't enough cash.
- `POST /api/approvals/{id}/reject`: a human rejects a prepared payment or purchase order; no cash moves.
- `GET /api/cash`: current checking balance from `cash_accounts`, plus the total waiting for approval.
- `POST /api/reset`: copies `data/campus_customs.db` over `data/campus_customs_new.db` for a fresh run (refuses while agents are running; keeps the audit trail).
- `GET /api/health`: server check (model name, whether an agent run is in progress).
