#!/usr/bin/env python3
"""
Turn Square's "Items Detail" order export + a "Customers" export into:
  1. raffle_tickets.csv   - one row per physical ticket, numbered per prize
  2. raffle_tickets.pdf   - printable ticket stubs, ready to cut and drop
                            in the drawing box alongside in-person tickets

Usage:
  python3 build_raffle_tickets.py --items ITEMS_DETAIL.csv --customers CUSTOMERS.csv --out-dir OUT

Quirks this script accounts for (Square's export, observed 2026-08-26):
  - Qty is always 1.0, even for a "3 for $12" bundle. The real ticket
    count is embedded in the "Price Point Name" column (e.g. "3 for $12").
  - Items Detail has no phone/email - only Customer Name + Square Customer
    ID. Contact info comes from the separate Customers export, joined on
    "Square Customer ID".
"""
import argparse
import csv
import re
from pathlib import Path

PRIZE_KEYWORDS = [
    ("cooler", "Taiga Cooler"),
    ("bottle", "Champions Edition Bottle"),
    ("buckle", "Anniversary Buckle"),
    ("purse", "Leather Purse"),
    ("hat", "Hat Co."),
]

TICKET_COUNT_RE = re.compile(r"(\d+)\s+for")


def prize_code(item_name):
    for code, needle in PRIZE_KEYWORDS:
        if needle.lower() in item_name.lower():
            return code
    return re.sub(r"[^a-z0-9]+", "-", item_name.lower()).strip("-")[:20]


def ticket_count(price_point_name, qty):
    m = TICKET_COUNT_RE.search(price_point_name or "")
    per_line = int(m.group(1)) if m else 1
    try:
        qty = int(float(qty))
    except (TypeError, ValueError):
        qty = 1
    return per_line * max(qty, 1)


def load_customers(path):
    lookup = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            cid = row.get("Square Customer ID", "").strip()
            if not cid:
                continue
            phone = row.get("Phone Number", "").strip().lstrip("'")
            lookup[cid] = {
                "name": f"{row.get('First Name', '').strip()} {row.get('Last Name', '').strip()}".strip(),
                "phone": phone,
                "email": row.get("Email Address", "").strip(),
            }
    return lookup


def build_tickets(items_path, customers_path):
    customers = load_customers(customers_path)
    counters = {}
    tickets = []
    skipped = []

    with open(items_path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            item_name = row.get("Item", "").strip()
            if not item_name:
                continue
            code = prize_code(item_name)
            count = ticket_count(row.get("Price Point Name", ""), row.get("Qty", "1"))
            cid = row.get("Customer ID", "").strip()
            info = customers.get(cid)
            buyer_name = row.get("Customer Name", "").strip() or (info["name"] if info else "")
            if not info:
                skipped.append((buyer_name or "(unknown)", item_name))

            for _ in range(count):
                counters[code] = counters.get(code, 0) + 1
                tickets.append({
                    "prize_code": code,
                    "prize_name": item_name,
                    "ticket_number": f"{code.upper()}-{counters[code]:03d}",
                    "buyer_name": buyer_name,
                    "phone": info["phone"] if info else "",
                    "email": info["email"] if info else "",
                    "date": row.get("Date", ""),
                    "transaction_id": row.get("Transaction ID", ""),
                })
    return tickets, skipped


def write_csv(tickets, out_path):
    fields = ["prize_code", "prize_name", "ticket_number", "buyer_name", "phone", "email", "date", "transaction_id"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(tickets)


def write_pdf(tickets, out_path):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas

    cols, rows = 3, 8
    margin = 0.4 * inch
    cell_w = (letter[0] - 2 * margin) / cols
    cell_h = (letter[1] - 2 * margin) / rows
    per_page = cols * rows

    c = canvas.Canvas(str(out_path), pagesize=letter)
    for i, t in enumerate(tickets):
        pos = i % per_page
        if pos == 0 and i > 0:
            c.showPage()
        col, row = pos % cols, pos // cols
        x = margin + col * cell_w
        y = letter[1] - margin - (row + 1) * cell_h

        c.setDash(2, 2)
        c.rect(x, y, cell_w, cell_h)
        c.setDash()

        pad = 8
        c.setFont("Helvetica-Bold", 13)
        c.drawString(x + pad, y + cell_h - 20, t["ticket_number"])
        c.setFont("Helvetica", 8)
        c.drawString(x + pad, y + cell_h - 34, t["prize_name"][:34])
        c.setFont("Helvetica", 9)
        c.drawString(x + pad, y + 22, (t["buyer_name"] or "(name missing)")[:30])
        c.setFont("Helvetica", 7)
        c.drawString(x + pad, y + 10, "TETWP Raffle • Sept 17, 2026")
    c.showPage()
    c.save()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True, help="Square 'Items Detail' export CSV")
    ap.add_argument("--customers", required=True, help="Square 'Customers' export CSV")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tickets, skipped = build_tickets(args.items, args.customers)
    write_csv(tickets, out_dir / "raffle_tickets.csv")
    write_pdf(tickets, out_dir / "raffle_tickets.pdf")

    print(f"{len(tickets)} tickets written across {len(set(t['prize_code'] for t in tickets))} prize(s).")
    if skipped:
        print(f"WARNING: {len(skipped)} line item(s) had no matching customer contact info:")
        for name, item in skipped:
            print(f"  - {name} / {item}")


if __name__ == "__main__":
    main()
