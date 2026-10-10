# Campus Customs MCP Server

An MCP server, built with FastMCP, that is the agent team's only way to touch shop data. Tools return only what is stored, and when a record is missing they return `found: false` / `ok: false` instead of guessing. Write tools never move money or contact anyone: payments and purchase orders are queued for human approval, and customer messages are saved as drafts.

**Database:** `data/campus_customs_new.db` (the working copy; the original `data/campus_customs.db` is never touched). On startup the server adds two tables to the working copy if they're missing: `approval_queue` and `message_drafts`.

## Tools

| Tool | Inputs | Tables | Returns / does |
|---|---|---|---|
| `get_desk_date` | none | desk | The shop's "today" (`date_today`) and notes |
| `list_tickets` | `status` (default "open") | tickets | Tickets with that status, oldest first |
| `get_ticket` | `ticket_id` | tickets | Every field of one ticket |
| `check_stock` | `sku`, `size` | inventory, pricing | Quantity in stock, location, unit cost, list price |
| `list_vendors` | none | vendors | All vendors with specialty and lead time |
| `get_vendor_invoices` | `vendor_id` | vendors, invoices | Vendor details and lead time, open (unpaid) invoices, and their total |
| `get_invoice` | `invoice_id` | invoices, vendors | One invoice with its vendor's name and lead time |
| `get_lease` | `lease_id` | leases | Space, landlord, monthly rent, next due date |
| `get_cash_balance` | `account` (default "checking") | cash_accounts, approval_queue | Balance, total waiting for approval, and what's left after that |
| `list_pending_approvals` | none | approval_queue | Payments and purchase orders waiting for approval |
| `prepare_payment` | `ticket_id`, `ref_type` ("invoice" or "lease"), `ref_id`, `amount`, `reason`, `requested_by`, `account` | invoices / leases, cash_accounts → approval_queue | Queues a payment for approval. Refuses over-amounts, non-open invoices, duplicates, or anything that would take cash below zero |
| `prepare_purchase_order` | `ticket_id`, `vendor_id`, `sku`, `size`, `qty`, `reason`, `requested_by`, `account` | inventory, pricing, vendors, invoices, cash_accounts → approval_queue | Queues a restock priced at `unit_cost` × qty. Refuses if cash would go below zero, and warns if the vendor has unpaid invoices |
| `save_customer_draft` | `ticket_id`, `recipient`, `subject`, `body`, `drafted_by` | message_drafts | Saves a draft (never sent) |
| `resolve_ticket` | `ticket_id`, `resolution` | tickets | Sets status to "resolved" and appends the resolution to the notes |

## Run

```bash
.venv/bin/python mcp_server/server.py
```

It's registered for Claude Code in `.mcp.json`. The agent team in `backend/agents.py` starts it over stdio.
