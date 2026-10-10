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
