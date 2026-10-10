"""Campus Customs MCP server.

Exposes database lookups to the agent team as MCP tools. All tools read from
the working copy data/campus_customs_new.db and only return what is stored
there; if a record is missing, the tool says so instead of guessing.
"""

import sqlite3
from pathlib import Path

from fastmcp import FastMCP

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "campus_customs_new.db"

mcp = FastMCP("campus-customs")


def query(sql: str, params: tuple = ()) -> list[dict]:
    """Run a read-only query and return rows as dicts."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


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


if __name__ == "__main__":
    mcp.run()
