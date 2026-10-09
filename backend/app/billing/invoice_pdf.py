"""Renders an invoice, guest statement or credit note to PDF from its issued data.

The document carries what the security spec requires of a tax invoice: the title, supplier
name, address and VAT number, recipient details where required, the serial number, issue
date, the supplies, their value and the VAT included at the rate applied. Tips are shown
apart from the bill because they are not a supply.

Only the PDF core fonts are used (no font files to ship); text outside Latin-1 is replaced.
"""

from __future__ import annotations

from typing import Any

from fpdf import FPDF
from fpdf.enums import XPos, YPos

NAVY = (11, 35, 80)
GREY = (90, 98, 112)
LINE = (214, 220, 228)
NEXT_LINE: dict[str, Any] = {"new_x": XPos.LMARGIN, "new_y": YPos.NEXT}


def amount(minor: int, currency: str) -> str:
    sign = "-" if minor < 0 else ""
    whole, cents = divmod(abs(int(minor)), 100)
    symbol = "R " if currency == "ZAR" else f"{currency} "
    return f"{sign}{symbol}{whole:,}.{cents:02d}"


def _t(value: Any) -> str:
    return str(value if value is not None else "").encode("latin-1", "replace").decode("latin-1")


def _address_lines(address: dict[str, Any] | None) -> list[str]:
    a = address or {}
    city = " ".join(p for p in (a.get("city"), a.get("postal_code")) if p)
    return [p for p in (a.get("line1"), a.get("line2"), city, a.get("province"), a.get("country")) if p]


class _Doc(FPDF):
    def footer(self) -> None:
        self.set_y(-14)
        self.set_font("Helvetica", size=8)
        self.set_text_color(*GREY)
        self.cell(0, 6, f"Page {self.page_no()} of {{nb}}", align="C")

    @property
    def width(self) -> float:
        return float(self.w - self.l_margin - self.r_margin)


def _heading(pdf: _Doc, doc: dict[str, Any]) -> None:
    w = pdf.width
    pdf.set_text_color(*NAVY)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(w / 2, 10, _t(doc["title"]))
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(w / 2, 10, _t(f"No. {doc['number']}"), align="R", **NEXT_LINE)
    pdf.set_font("Helvetica", size=9)
    pdf.set_text_color(*GREY)
    pdf.cell(w, 5, _t(f"Issued {doc['issued_at']}"), align="R", **NEXT_LINE)
    if doc.get("credits_number"):
        pdf.cell(w, 5, _t(f"Cancels {doc['credits_number']}"), align="R", **NEXT_LINE)
    pdf.ln(4)


def _parties(pdf: _Doc, supplier: dict[str, Any], recipient: dict[str, Any]) -> None:
    left = [supplier.get("name")]
    if supplier.get("trading_name") and supplier["trading_name"] != supplier.get("name"):
        left.append(f"Trading as {supplier['trading_name']}")
    left += _address_lines(supplier.get("address"))
    if supplier.get("vat_number"):
        left.append(f"VAT number {supplier['vat_number']}")
    left += [p for p in (supplier.get("phone"), supplier.get("email")) if p]

    right = [recipient.get("name"), *_address_lines(recipient.get("address"))]
    for key, label in (
        ("registration_number", "Registration"),
        ("vat_number", "VAT number"),
        ("purchase_order", "Order no."),
        ("traveller", "Traveller"),
    ):
        if recipient.get(key):
            right.append(f"{label} {recipient[key]}")

    half = pdf.width / 2
    top = pdf.get_y()
    for col, (heading, lines) in enumerate((("From", left), ("To", right))):
        pdf.set_xy(pdf.l_margin + col * half, top)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*GREY)
        pdf.cell(half, 5, heading, new_x=XPos.LEFT, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)
        for i, line in enumerate(p for p in lines if p):
            pdf.set_font("Helvetica", "B" if i == 0 else "", 10 if i == 0 else 9)
            pdf.cell(half, 5, _t(line), new_x=XPos.LEFT, new_y=YPos.NEXT)
    pdf.set_y(top + 5 + 5 * max(len(left), len(right)) + 6)


def _lines(pdf: _Doc, items: list[dict[str, Any]], currency: str) -> None:
    cols = (pdf.width - 60, 14, 18, 28)
    pdf.set_draw_color(*LINE)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*GREY)
    for w, label, align in zip(cols, ("Description", "Qty", "VAT", "Amount"), "LRRR", strict=True):
        pdf.cell(w, 7, label, border="B", align=align)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", size=9)
    for item in items:
        vat = f"{item['vat_rate_bp'] / 100:g}%" if item["vat_rate_bp"] else "-"
        pdf.cell(cols[0], 6, _t(item["description"])[:90])
        pdf.cell(cols[1], 6, str(item["quantity"]), align="R")
        pdf.cell(cols[2], 6, vat, align="R")
        pdf.cell(cols[3], 6, amount(item["amount_minor"], currency), align="R", **NEXT_LINE)
    if not items:
        pdf.set_text_color(*GREY)
        pdf.cell(pdf.width, 6, "No charges.", **NEXT_LINE)
        pdf.set_text_color(0, 0, 0)
    pdf.ln(3)


def _totals(pdf: _Doc, doc: dict[str, Any]) -> None:
    c, t = doc["currency"], doc["totals"]

    def row(label: str, value: int, bold: bool = False) -> None:
        pdf.set_font("Helvetica", "B" if bold else "", 10 if bold else 9)
        pdf.cell(pdf.width - 40, 6, _t(label), align="R")
        pdf.cell(40, 6, amount(value, c), align="R", **NEXT_LINE)

    for key, label in (
        ("accommodation_minor", "Accommodation"),
        ("fnb_minor", "Food and beverage"),
        ("other_minor", "Other services"),
    ):
        if t[key]:
            row(label, t[key])
    row("Total", t["charges_minor"], bold=True)
    if doc["vat_registered"]:
        row(f"VAT included at {doc['vat_rate_bp'] / 100:g}%", t["vat_minor"])
    if doc["kind"] != "credit_note":
        row("Payments received", t["paid_minor"])
        row("Balance due", t["balance_minor"], bold=True)
    pdf.ln(4)


def _notes(pdf: _Doc, doc: dict[str, Any]) -> None:
    c, t = doc["currency"], doc["totals"]
    notes = []
    if doc["kind"] != "credit_note" and t.get("tips_minor"):
        notes.append(
            f"Tips of {amount(t['tips_minor'], c)} were received for staff. They are not part of this "
            "bill and carry no VAT."
        )
    if not doc["vat_registered"]:
        notes.append("The supplier is not registered for VAT; no VAT is charged.")
    if "long_stay" in t.get("flags", []):
        notes.append("Stay longer than 28 days: the hotel confirmed the accommodation charges at checkout.")
    if doc.get("reason"):
        notes.append(f"Reason: {doc['reason']}")
    pdf.set_font("Helvetica", size=8)
    pdf.set_text_color(*GREY)
    for note in notes:
        pdf.multi_cell(pdf.width, 4.5, _t(note), **NEXT_LINE)


def render(doc: dict[str, Any]) -> bytes:
    pdf = _Doc(format="A4")
    pdf.set_title(_t(f"{doc['title']} {doc['number']}"))
    pdf.set_creator("Diyneco")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(True, margin=20)
    pdf.add_page()
    _heading(pdf, doc)
    _parties(pdf, doc["supplier"], doc["recipient"])
    _lines(pdf, doc["items"], doc["currency"])
    _totals(pdf, doc)
    _notes(pdf, doc)
    return bytes(pdf.output())
