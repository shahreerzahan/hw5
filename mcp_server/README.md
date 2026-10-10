# Campus Customs MCP Server

An MCP server, built with FastMCP, that gives the Campus Customs agent team read-only lookups into the shop's database. The agents use it to answer the open tickets from real data. Tools return only what is stored, and when a record is missing they return `found: false` instead of guessing.

**Database:** `data/campus_customs_new.db` (the working copy; the original `data/campus_customs.db` is never touched).

## Tools

| Tool | Inputs | Reads | Returns |
|---|---|---|---|
| `check_stock` | `sku`, `size` | inventory, pricing | Quantity in stock, location, unit cost, list price |
| `get_vendor_invoices` | `vendor_id` | vendors, invoices | Vendor details and lead time, open (unpaid) invoices, and their total |
| `get_lease` | `lease_id` | leases | Space, landlord, monthly rent, next due date |

## Run

```bash
.venv/bin/python mcp_server/server.py
```
