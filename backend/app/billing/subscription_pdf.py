"""Renders Diyneco's invoice or credit note to a hotel (DECISIONS D78) from its issued data.

Everything printed comes from the invoice's own copy of the seller, the buyer, the tax and the
amounts, so a PDF regenerated later is identical. "Tax invoice" and a VAT number appear only
when Diyneco was VAT-registered on the issue date; otherwise it is a plain invoice. Missing
company details are left out, never invented.
"""

from __future__ import annotations

from typing import Any

from app.billing.invoice_pdf import GREY, LINE, NAVY, NEXT_LINE, _address_lines, _Doc, _t, amount

TITLES = {
    ("invoice", True): "Tax invoice",
    ("invoice", False): "Invoice",
    ("credit_note", True): "Credit note",
    ("credit_note", False): "Credit note",
}


def _block(pdf: _Doc, x: float, y: float, w: float, title: str, rows: list[str]) -> float:
    pdf.set_xy(x, y)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*GREY)
    pdf.cell(w, 5, _t(title), **NEXT_LINE)
    pdf.set_text_color(20, 20, 20)
    for i, row in enumerate(r for r in rows if r):
        pdf.set_x(x)
        pdf.set_font("Helvetica", "B" if i == 0 else "", 10 if i == 0 else 9)
        pdf.multi_cell(w, 5, _t(row), **NEXT_LINE)
    return float(pdf.get_y())


def _header(pdf: _Doc, inv: dict[str, Any], logo: bytes | None) -> None:
    w = pdf.width
    if logo:
        try:
            pdf.image(logo, x=pdf.l_margin, y=pdf.t_margin, h=14)
            pdf.ln(16)
        except Exception:
            pdf.ln(2)
    title = TITLES[(inv["kind"], bool(inv["is_tax_invoice"]))]
    pdf.set_text_color(*NAVY)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(w / 2, 10, _t(title))
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(w / 2, 10, _t(f"No. {inv['number']}"), align="R", **NEXT_LINE)
    pdf.set_font("Helvetica", size=9)
    pdf.set_text_color(*GREY)
    meta = [f"Issued {inv['issued_on']}"]
    if inv.get("due_on") and inv["kind"] == "invoice":
        meta.append(f"Due {inv['due_on']}")
    if inv.get("credits_number"):
        meta.append(f"Credits invoice {inv['credits_number']}")
    for m in meta:
        pdf.cell(w, 5, _t(m), align="R", **NEXT_LINE)
    pdf.ln(4)


def _parties(pdf: _Doc, inv: dict[str, Any]) -> None:
    w, seller, buyer = pdf.width, inv["seller"], inv["buyer"]
    top = float(pdf.get_y())
    seller_rows = [
        seller.get("legal_name"),
        f"Trading as {seller['trading_name']}" if seller.get("trading_name") else None,
        f"Registration no. {seller['registration_number']}" if seller.get("registration_number") else None,
        *(_address_lines(seller.get("registered_address"))),
        f"VAT no. {seller['vat_number']}" if inv["is_tax_invoice"] and seller.get("vat_number") else None,
        seller.get("billing_email"),
        seller.get("billing_phone"),
    ]
    buyer_rows = [
        buyer.get("legal_name") or buyer.get("hotel_name"),
        f"Trading as {buyer['hotel_name']}"
        if buyer.get("legal_name") and buyer.get("hotel_name") != buyer.get("legal_name")
        else None,
        *(_address_lines(buyer.get("address"))),
        f"VAT no. {buyer['vat_number']}" if buyer.get("vat_number") else None,
        buyer.get("contact_name"),
        buyer.get("billing_email"),
    ]
    end_left = _block(pdf, pdf.l_margin, top, w / 2 - 4, "From", [r for r in seller_rows if r])
    end_right = _block(pdf, pdf.l_margin + w / 2 + 4, top, w / 2 - 4, "Bill to", [r for r in buyer_rows if r])
    pdf.set_y(max(end_left, end_right) + 4)
    if inv.get("period_start") and inv.get("period_end"):
        pdf.set_font("Helvetica", size=9)
        pdf.set_text_color(*GREY)
        pdf.cell(w, 5, _t(f"Service period {inv['period_start']} to {inv['period_end']}"), **NEXT_LINE)
        pdf.ln(2)


def _table(pdf: _Doc, inv: dict[str, Any], lines: list[dict[str, Any]]) -> None:
    w, cur = pdf.width, inv["currency"]
    tax_name = inv.get("tax_name") or "VAT"
    cols = [w * 0.46, w * 0.08, w * 0.15, w * 0.15, w * 0.16]
    pdf.set_fill_color(*NAVY)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    heads = ["Description", "Qty", "Unit price", tax_name if inv["is_tax_invoice"] else "Discount", "Amount"]
    for i, (head, cw) in enumerate(zip(heads, cols, strict=True)):
        pdf.cell(cw, 8, _t(head), fill=True, align="L" if i == 0 else "R")
    pdf.ln(8)
    pdf.set_text_color(20, 20, 20)
    pdf.set_font("Helvetica", size=9)
    pdf.set_draw_color(*LINE)
    for line in lines:
        middle = line["tax_minor"] if inv["is_tax_invoice"] else line["discount_minor"]
        desc = line["description"]
        if inv["is_tax_invoice"] and line["discount_minor"]:
            desc += f" (less {amount(line['discount_minor'], cur)})"
        pdf.cell(cols[0], 7, _t(desc), border="B")
        pdf.cell(cols[1], 7, str(line["quantity"]), border="B", align="R")
        pdf.cell(cols[2], 7, _t(amount(line["unit_amount_minor"], cur)), border="B", align="R")
        pdf.cell(cols[3], 7, _t(amount(middle, cur)), border="B", align="R")
        pdf.cell(cols[4], 7, _t(amount(line["total_minor"], cur)), border="B", align="R", **NEXT_LINE)


def _totals(pdf: _Doc, inv: dict[str, Any]) -> None:
    w, cur = pdf.width, inv["currency"]
    pdf.ln(3)
    rows = [("Subtotal", inv["subtotal_minor"])]
    if inv["is_tax_invoice"]:
        rows.append((f"{inv.get('tax_name') or 'VAT'} at {inv['tax_rate_bp'] / 100:g}%", inv["tax_minor"]))
    rows.append(("Total" if inv["kind"] == "invoice" else "Total credited", inv["total_minor"]))
    if inv["kind"] == "invoice":
        rows.append(("Paid", inv.get("paid_minor", 0)))
        rows.append(("Balance due", inv["total_minor"] - inv.get("paid_minor", 0)))
    for label, value in rows:
        bold = label in ("Total", "Total credited", "Balance due")
        pdf.set_font("Helvetica", "B" if bold else "", 10 if bold else 9)
        pdf.cell(w * 0.7, 6, _t(label), align="R")
        pdf.cell(w * 0.3, 6, _t(amount(value, cur)), align="R", **NEXT_LINE)
    pdf.set_font("Helvetica", size=8)
    pdf.set_text_color(*GREY)
    pdf.cell(
        w, 5, _t(f"Amounts in {cur}. Status: {inv['status'].replace('_', ' ')}."), align="R", **NEXT_LINE
    )


def _how_to_pay(pdf: _Doc, inv: dict[str, Any]) -> None:
    w, bank = pdf.width, inv["seller"].get("bank") or {}
    if inv["kind"] != "invoice" or not (inv.get("payment_instructions") or bank):
        return
    pdf.ln(4)
    pdf.set_text_color(20, 20, 20)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(w, 5, "How to pay", **NEXT_LINE)
    pdf.set_font("Helvetica", size=9)
    for label, key in (
        ("Bank", "bank_name"),
        ("Account holder", "account_holder"),
        ("Account number", "account_number"),
        ("Branch code", "branch_code"),
        ("SWIFT", "swift_code"),
    ):
        if bank.get(key):
            pdf.cell(w, 5, _t(f"{label}: {bank[key]}"), **NEXT_LINE)
    pdf.cell(w, 5, _t(f"Reference: {inv['number']}"), **NEXT_LINE)
    if inv.get("payment_instructions"):
        pdf.multi_cell(w, 5, _t(inv["payment_instructions"]), **NEXT_LINE)


def render(inv: dict[str, Any], lines: list[dict[str, Any]], logo: bytes | None = None) -> bytes:
    pdf = _Doc(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.alias_nb_pages()
    pdf.add_page()
    _header(pdf, inv, logo)
    _parties(pdf, inv)
    _table(pdf, inv, lines)
    _totals(pdf, inv)
    _how_to_pay(pdf, inv)
    if inv.get("notes"):
        pdf.ln(3)
        pdf.set_font("Helvetica", size=9)
        pdf.multi_cell(pdf.width, 5, _t(inv["notes"]), **NEXT_LINE)
    return bytes(pdf.output())
