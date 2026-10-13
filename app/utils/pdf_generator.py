from __future__ import annotations

import os
import sys
from collections import defaultdict
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                Paragraph, Spacer, Image)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.units import mm
from app.config.settings import REPORTS_DIR

os.makedirs(REPORTS_DIR, exist_ok=True)

PAGE_WIDTH = 535  # usable width with 30pt margins on A4


def _get_logo_path():
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.join(base_path, "..", "..")
    return os.path.join(base_path, "logo.png")


def _resolve_logo_path(company_logo_path: str = "") -> str:
    """
    Dynamic company logo resolution: if a logo path was registered/saved
    in Settings (company_logo_path, stored on the User row), use that.
    Otherwise fall back to the bundled logo.png (old static behavior),
    and if neither exists, no logo is drawn at all -- never crashes on
    a missing/typo'd path.
    """
    if company_logo_path and os.path.exists(company_logo_path):
        return company_logo_path
    return _get_logo_path()


_ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight",
         "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen",
         "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
_TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy",
         "Eighty", "Ninety"]


def _two_digits(n: int) -> str:
    if n < 20:
        return _ONES[n]
    return (_TENS[n // 10] + (" " + _ONES[n % 10] if n % 10 else "")).strip()


def _three_digits(n: int) -> str:
    if n >= 100:
        return (_ONES[n // 100] + " Hundred" +
                (" " + _two_digits(n % 100) if n % 100 else "")).strip()
    return _two_digits(n)


def amount_to_words(amount: float) -> str:
    rupees = int(round(amount))
    if rupees == 0:
        return "Zero Rupees Only"

    crore = rupees // 10000000
    rupees %= 10000000
    lakh = rupees // 100000
    rupees %= 100000
    thousand = rupees // 1000
    rupees %= 1000
    hundred = rupees

    parts = []
    if crore:
        parts.append(_three_digits(crore) + " Crore")
    if lakh:
        parts.append(_three_digits(lakh) + " Lakh")
    if thousand:
        parts.append(_three_digits(thousand) + " Thousand")
    if hundred:
        parts.append(_three_digits(hundred))

    return " ".join(parts).strip() + " Rupees Only"


def generate_invoice_pdf(sale_obj, company_name="Dindigul School Point",
                         company_address="", company_gst="",
                         company_phone="", company_email="",
                         company_logo_path=""):
    file_path = os.path.join(REPORTS_DIR, f"Invoice_{sale_obj.id}.pdf")
    doc = SimpleDocTemplate(file_path, pagesize=A4,
                           topMargin=20, bottomMargin=20,
                           leftMargin=30, rightMargin=30)
    elements = []
    styles = getSampleStyleSheet()

    style_center_normal = styles["Normal"].clone("CenterNormal")
    style_center_normal.alignment = TA_CENTER
    style_center_normal.fontSize = 9
    style_center_normal.fontName = "Times-Roman"

    style_center_h2 = styles["Heading2"].clone("CenterH2")
    style_center_h2.alignment = TA_CENTER
    style_center_h2.fontName = "Times-Bold"

    style_left_normal = styles["Normal"].clone("LeftNormal")
    style_left_normal.alignment = TA_LEFT
    style_left_normal.fontSize = 9
    style_left_normal.leading = 13
    style_left_normal.fontName = "Times-Roman"

    style_right_normal = styles["Normal"].clone("RightNormal")
    style_right_normal.alignment = TA_RIGHT
    style_right_normal.fontSize = 9
    style_right_normal.leading = 13
    style_right_normal.fontName = "Times-Roman"

    title_text = "TAX INVOICE" if sale_obj.is_gst_bill else "RETAIL INVOICE"

    # ── Header: logo left (dynamic, from registration/settings) + company details centered ──
    logo_path = _resolve_logo_path(company_logo_path)

    def _make_logo():
        if os.path.exists(logo_path):
            img = Image(logo_path, width=35 * mm, height=20 * mm)
            img.hAlign = "LEFT"
            return img
        return Paragraph("", style_center_normal)

    logo_left = _make_logo()

    company_lines = [f'<font size="16"><b>{company_name.upper()}</b></font>']
    if company_address:
        company_lines.append(f'<font size="11">{company_address.replace(chr(10), "<br/>")}</font>')
    contact_bits = []
    if company_phone:
        contact_bits.append(f"Phone: {company_phone}")
    if company_email:
        contact_bits.append(f"Email: {company_email}")
    if contact_bits:
        company_lines.append(f'<font size="11">{" | ".join(contact_bits)}</font>')
    if sale_obj.is_gst_bill and company_gst:
        company_lines.append(f'<font size="11"><b>GSTIN:</b> {company_gst}</font>')

    company_para = Paragraph("<br/>".join(company_lines), style_center_normal)

    header_table = Table(
        [[logo_left, company_para, ""]],
        colWidths=[
            PAGE_WIDTH * 0.18,   # Logo
            PAGE_WIDTH * 0.64,   # Company Details
            PAGE_WIDTH * 0.18    # Empty (balances logo)
        ]
    )

    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),

        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 0),

        ("LEFTPADDING", (1, 0), (1, 0), 0),
        ("RIGHTPADDING", (1, 0), (1, 0), 0),

        ("LEFTPADDING", (2, 0), (2, 0), 0),
        ("RIGHTPADDING", (2, 0), (2, 0), 0),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(title_text, style_center_h2))
    elements.append(Spacer(1, 10))

    # ── Receiver + Invoice info ─────────────────────────────────────────
    receiver_lines = [
        "<b font-size='16'>Bill To:</b>",
        f"<b font-size='14'>Name: </b>{sale_obj.customer_name or 'Walk-in Customer'}",
    ]
    if sale_obj.customer_phone:
        receiver_lines.append(f"<b font-size='14'>Phone: </b> {sale_obj.customer_phone}")
    customer_address = getattr(sale_obj, "customer_address", "") or ""
    if customer_address:
        receiver_lines.append(f"<b font-size='14'>Address: </b> {customer_address}")
    customer_gstin = getattr(sale_obj, "customer_gstin", "") or ""
    if customer_gstin:
        receiver_lines.append(f"<b font-size='14'>GSTIN: </b> {customer_gstin}")
    receiver_para = Paragraph("<br/>".join(receiver_lines), style_left_normal)

    invoice_lines = [
        f"<b font-size: '18'>Invoice #:  </b><div font-size:'16'>{sale_obj.id}</div>",
        f"<b font-size: '18'>Date:  </b> <div font-size:'16'>{sale_obj.date_created.strftime('%d-%m-%Y %H:%M')}</div>",
    ]
    invoice_para = Paragraph("<br/>".join(invoice_lines), style_left_normal)

    info_table = Table([[receiver_para, invoice_para]],
                       colWidths=[PAGE_WIDTH * 0.6, PAGE_WIDTH * 0.4])
    info_table.setStyle(TableStyle([
        ("BOX", (0, 0), (0, 0), 1, colors.black),
        ("BOX", (1, 0), (1, 0), 1, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 14))

    # ── Item table with Adjusted Widths & No Rs. Prefix ──────────────────
    rate_groups = defaultdict(lambda: {"taxable": 0.0, "gst": 0.0})

    discount_amt = getattr(sale_obj, "discount_amount", 0.0) or 0.0
    discount_pct = getattr(sale_obj, "discount_percentage", 0.0) or 0.0

    if sale_obj.is_gst_bill:
        data = [["Item Name", "Size", "Qty", "Unit Price", "Amount", "GST %", "GST Amt"]]
        for item in sale_obj.items:
            item_gst_rate = getattr(item, "gst_rate", 0.0) or 0.0
            item_gst_amt = item.total_price * (item_gst_rate / 100)
            rate_groups[item_gst_rate]["taxable"] += item.total_price
            rate_groups[item_gst_rate]["gst"] += item_gst_amt
            data.append([
                item.product_name,
                getattr(item, "size", "") or "-",
                str(item.quantity),
                f"{item.unit_price:.2f}",
                f"{item.total_price:.2f}",
                f"{item_gst_rate:.0f}%",
                f"{item_gst_amt:.2f}",
            ])

        data.append(["", "", "", "", Paragraph("<b>Subtotal:</b>", style_right_normal), "", f"{sale_obj.subtotal:.2f}"])

        if discount_amt > 0:
            data.append(["", "", "", "", Paragraph(f"<b>Discount ({discount_pct:.1f}%):</b>", style_right_normal), "", f"-{discount_amt:.2f}"])

        if sale_obj.gst_amount > 0:
            for rate, vals in sorted(rate_groups.items()):
                if vals["gst"] > 0:
                    half_rate = rate / 2
                    half_amount = vals["gst"] / 2
                    data.append(["", "", "", "", Paragraph(f"<b>CGST ({half_rate:.1f}%):</b>", style_right_normal), "", f"{half_amount:.2f}"])
                    data.append(["", "", "", "", Paragraph(f"<b>SGST ({half_rate:.1f}%):</b>", style_right_normal), "", f"{half_amount:.2f}"])

        data.append(["", "", "", "", Paragraph("<b>GRAND TOTAL:</b>", style_right_normal), "", f"{sale_obj.total_amount:.2f}"])

        paid_amount = getattr(sale_obj, "paid_amount", sale_obj.total_amount) or 0.0
        due_amount = getattr(sale_obj, "due_amount", 0.0) or 0.0
        data.append(["", "", "", "", Paragraph("<b>Amount Paid:</b>", style_right_normal), "", f"{paid_amount:.2f}"])
        due_row_index = None
        if due_amount > 0.001:
            due_row_index = len(data)
            data.append(["", "", "", "", Paragraph("<b>BALANCE DUE:</b>", style_right_normal), "", f"{due_amount:.2f}"])

        # GST Bill Column Widths (Item, Size, Qty, Price, Amount, GST%, GST Amt)
        col_widths = [PAGE_WIDTH * 0.18, PAGE_WIDTH * 0.18, PAGE_WIDTH * 0.07,
                      PAGE_WIDTH * 0.12, PAGE_WIDTH * 0.20, PAGE_WIDTH * 0.08,
                      PAGE_WIDTH * 0.17]

    else:
        data = [["Item Name", "Size", "Qty", "Unit Price", "Total"]]
        for item in sale_obj.items:
            data.append([
                item.product_name,
                getattr(item, "size", "") or "-",
                str(item.quantity),
                f"{item.unit_price:.2f}",
                f"{item.total_price:.2f}",
            ])
        data.append(["", "", "", Paragraph("<b>Subtotal:</b>", style_right_normal), f"{sale_obj.subtotal:.2f}"])

        if discount_amt > 0:
            data.append(["", "", "", Paragraph(f"<b>Discount ({discount_pct:.1f}%):</b>", style_right_normal), f"-{discount_amt:.2f}"])

        data.append(["", "", "", Paragraph("<b>GRAND TOTAL:</b>", style_right_normal), f"{sale_obj.total_amount:.2f}"])

        paid_amount = getattr(sale_obj, "paid_amount", sale_obj.total_amount) or 0.0
        due_amount = getattr(sale_obj, "due_amount", 0.0) or 0.0
        data.append(["", "", "", Paragraph("<b>Amount Paid:</b>", style_right_normal), f"{paid_amount:.2f}"])
        due_row_index = None
        if due_amount > 0.001:
            due_row_index = len(data)
            data.append(["", "", "", Paragraph("<b>BALANCE DUE:</b>", style_right_normal), f"{due_amount:.2f}"])

        # Retail Bill Column Widths (Item, Size, Qty, Unit Price, Total) - Increased Size column here too
        col_widths = [PAGE_WIDTH * 0.24, PAGE_WIDTH * 0.22, PAGE_WIDTH * 0.10,
                      PAGE_WIDTH * 0.22, PAGE_WIDTH * 0.22]
 
    table = Table(data, colWidths=col_widths)
    style_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -2), 1, colors.black),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTNAME", (0, due_row_index - 1 if due_row_index else -1),
                     (-1, due_row_index - 1 if due_row_index else -1), "Helvetica-Bold"),
    ]
    if due_row_index is not None:
        style_commands.append(("TEXTCOLOR", (0, due_row_index), (-1, due_row_index), colors.red))
        style_commands.append(("FONTNAME", (0, due_row_index), (-1, due_row_index), "Helvetica-Bold"))

    table.setStyle(TableStyle(style_commands))
    elements.append(table)
    elements.append(Spacer(1, 14))

    # ── Tax Summary table ────────────────────────────────────────────────
    if sale_obj.is_gst_bill and sale_obj.gst_amount > 0:
        tax_data = [["Tax Rate", "Taxable Amount", "CGST", "SGST", "IGST", "Total Tax"]]
        for rate, vals in sorted(rate_groups.items()):
            if vals["gst"] <= 0:
                continue
            half = vals["gst"] / 2
            tax_data.append([
                f"{rate:.0f}%",
                f"{vals['taxable']:.2f}",
                f"{half:.2f}",
                f"{half:.2f}",
                "0.00",
                f"{vals['gst']:.2f}",
            ])
        total_taxable = sum(v["taxable"] for v in rate_groups.values())
        tax_data.append([
            "Total", f"{total_taxable:.2f}",
            f"{sale_obj.gst_amount / 2:.2f}", f"{sale_obj.gst_amount / 2:.2f}",
            "0.00", f"{sale_obj.gst_amount:.2f}",
        ])

        tax_table = Table(tax_data, colWidths=[PAGE_WIDTH * x for x in
                                               (0.13, 0.22, 0.17, 0.17, 0.13, 0.18)])
        tax_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ]))
        elements.append(Paragraph("Tax Summary", style_left_normal))
        elements.append(Spacer(1, 4))
        elements.append(tax_table)
        elements.append(Spacer(1, 14))

    # ── Amount in words ────────────────────────────────────────────────
    words_style = styles["Normal"].clone("WordsStyle")
    words_style.fontSize = 9
    words_style.fontName = "Helvetica-Bold"
    elements.append(Paragraph(
        f"Amount in Words: {amount_to_words(sale_obj.total_amount)}",
        words_style,
    ))
    elements.append(Spacer(1, 20))

    # ── Terms & Conditions + Signature ───────────────────────────────────
    terms_title_style = styles["Heading4"].clone("TermsTitle")
    terms_title_style.alignment = TA_LEFT
    terms_title_style.fontSize = 10

    terms_style = styles["Normal"].clone("TermsBody")
    terms_style.alignment = TA_LEFT
    terms_style.fontSize = 8
    terms_style.leading = 11

    terms_list = [
        "Goods once sold will not be taken back or exchanged.",
        "Interest @18% will be charged on all overdue payments.",
        "All disputes are subject to local jurisdiction only.",
        "Please verify the items and quantity at the time of delivery.",
    ]
    terms_flow = [Paragraph("Terms and Conditions:", terms_title_style)]
    for i, term in enumerate(terms_list, start=1):
        terms_flow.append(Paragraph(f"{i}. {term}", terms_style))

    sig_style = styles["Normal"].clone("SigStyle")
    sig_style.alignment = TA_CENTER
    sig_style.fontSize = 9
    sig_flow = [
        Spacer(1, 40),
        Paragraph(f"For {company_name.upper()}", sig_style),
        Spacer(1, 30),
        Paragraph("Authorised Signatory", sig_style),
    ]

    footer_table = Table([[terms_flow, sig_flow]],
                         colWidths=[PAGE_WIDTH * 0.6, PAGE_WIDTH * 0.4])
    footer_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEABOVE", (1, 0), (1, 0), 0, colors.white),
    ]))
    elements.append(footer_table)
    elements.append(Spacer(1, 16))
    elements.append(Paragraph("Thank you for your business!", style_center_normal))
    doc.build(elements)
    return file_path


def generate_payment_receipt_pdf(
    sale_obj,
    payment_amount: float,
    payment_note: str = "",
    payment_date=None,
    company_name: str = "Dindigul School Point",
    company_address: str = "",
    company_gst: str = "",
    company_phone: str = "",
    company_logo_path: str = "",
):
    """
    Generates a professional PAYMENT RECEIPT matching the invoice format.
    Shows:
    - Company header with logo (same as invoice)
    - Original invoice details (items, subtotal, taxes, grand total)
    - Payment history (all installments to date)
    - Current payment received
    - Balance remaining
    - Professional styling matching the invoice PDF
    """
    from datetime import datetime
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from collections import defaultdict

    payment_date = payment_date or datetime.now()

    # Unique receipt file (same as before)
    existing = [
        f for f in os.listdir(REPORTS_DIR)
        if f.startswith(f"Receipt_{sale_obj.id}_")
    ]
    seq = len(existing) + 1
    file_path = os.path.join(REPORTS_DIR, f"Receipt_{sale_obj.id}_{seq}.pdf")

    doc = SimpleDocTemplate(
        file_path, pagesize=A4,
        topMargin=30, bottomMargin=30, leftMargin=40, rightMargin=40,
    )

    styles = getSampleStyleSheet()
    PAGE_WIDTH = A4[0] - 80

    # Define professional styles (matching invoice)
    title_style = styles["Title"].clone("TitleStyle")
    title_style.alignment = TA_CENTER
    title_style.fontSize = 18
    title_style.fontName = "Helvetica-Bold"
    title_style.textColor = colors.HexColor("#1a1a1a")

    subtitle_style = styles["Normal"].clone("SubtitleStyle")
    subtitle_style.alignment = TA_CENTER
    subtitle_style.fontSize = 9
    subtitle_style.textColor = colors.HexColor("#666666")

    heading_style = styles["Heading2"].clone("HeadingStyle")
    heading_style.alignment = TA_CENTER
    heading_style.fontSize = 14
    heading_style.fontName = "Helvetica-Bold"
    heading_style.textColor = colors.HexColor("#2c3e50")

    normal_style = styles["Normal"].clone("NormalStyle")
    normal_style.fontSize = 10
    normal_style.textColor = colors.HexColor("#333333")

    label_style = styles["Normal"].clone("LabelStyle")
    label_style.fontSize = 9
    label_style.fontName = "Helvetica-Bold"
    label_style.textColor = colors.HexColor("#2c3e50")

    style_right_normal = ParagraphStyle(
        "RightNormal",
        parent=styles["Normal"],
        alignment=TA_RIGHT,
        fontSize=10,
        textColor=colors.HexColor("#333333"),
    )

    style_center_normal = ParagraphStyle(
        "CenterNormal",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.HexColor("#333333"),
    )

    elements = []

    # ── HEADER: Logo + Company Name + Details ──
    logo_path = _resolve_logo_path(company_logo_path)
    if os.path.exists(logo_path):
        try:
            logo_img = Image(logo_path, width=30 * mm, height=20 * mm)
            logo_img.hAlign = "LEFT"
            elements.append(logo_img)
            elements.append(Spacer(1, 6))
        except Exception:
            pass

    elements.append(Paragraph(company_name.upper(), title_style))

    company_line = " | ".join(
        x for x in [company_address, f"GSTIN: {company_gst}" if company_gst else "",
                    f"Ph: {company_phone}" if company_phone else ""] if x
    )
    if company_line:
        elements.append(Paragraph(company_line, subtitle_style))

    elements.append(Spacer(1, 12))
    elements.append(Paragraph("PAYMENT RECEIPT", heading_style))
    elements.append(Spacer(1, 14))

    # ── RECEIPT INFO: Invoice # + Date + Customer ──
    info_data = [
        ["Receipt For Invoice #", f"#{sale_obj.id}", "Receipt Date", payment_date.strftime("%d-%m-%Y %H:%M")],
        ["Customer", sale_obj.customer_name or "Walk-in", "Phone", sale_obj.customer_phone or "-"],
    ]
    info_table = Table(info_data, colWidths=[110, 150, 90, 150])
    info_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#2c3e50")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8f9fa")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 16))

    # ── AMOUNT SUMMARY (Simple, no items table) ──
    elements.append(Paragraph("Amount Summary", label_style))
    elements.append(Spacer(1, 8))

    due_after = max(0.0, sale_obj.total_amount - sale_obj.paid_amount)
    status_after = "PAID IN FULL" if due_after <= 0.001 else "PARTIALLY PAID"

    summary_data = [
        ["Invoice Total", f"Rs. {sale_obj.total_amount:.2f}"],
        ["Amount Paid Now", f"Rs. {payment_amount:.2f}"],
        ["Balance Due", f"Rs. {due_after:.2f}"],
        ["Status", status_after],
    ]
    summary_table = Table(summary_data, colWidths=[200, 200])
    summary_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#2c3e50")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#ecf0f1")),
        ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#f8f9fa")),
        ("FONTNAME", (1, 1), (1, 1), "Helvetica-Bold"),
        ("TEXTCOLOR", (1, 1), (1, 1), colors.HexColor("#27ae60")),
        ("FONTNAME", (1, 3), (1, 3), "Helvetica-Bold"),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#bdc3c7")),
        ("LINEABOVE", (0, -1), (-1, -1), 0.5, colors.HexColor("#34495e")),
        ("LINEBELOW", (0, -1), (-1, -1), 1.5, colors.HexColor("#34495e")),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 16))

    # ── PAYMENT HISTORY TABLE ──
    all_payments = sorted(
        getattr(sale_obj, "payments", []) or [],
        key=lambda p: p.payment_date or datetime.now(),
    )

    if all_payments:
        elements.append(Paragraph("Payment History", label_style))
        elements.append(Spacer(1, 8))

        history_data = [["Payment #", "Date", "Amount", "Note"]]
        cumulative = 0.0
        for idx, payment in enumerate(all_payments, start=1):
            cumulative += payment.amount
            payment_dt = payment.payment_date.strftime("%d-%m-%Y %H:%M") if payment.payment_date else "N/A"
            history_data.append([
                str(idx),
                payment_dt,
                f"Rs. {payment.amount:.2f}",
                payment.note or "-",
            ])
        history_data.append(["", "TOTAL", f"Rs. {cumulative:.2f}", ""])

        history_table = Table(history_data, colWidths=[50, 110, 80, 160])
        history_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#ecf0f1")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
            ("ALIGN", (0, 0), (2, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(history_table)
        elements.append(Spacer(1, 16))

    if payment_note:
        note_style = styles["Normal"].clone("NoteStyle")
        note_style.fontSize = 9
        note_style.textColor = colors.HexColor("#555555")
        elements.append(Paragraph(f"<b>Note:</b> {payment_note}", note_style))
        elements.append(Spacer(1, 10))

    elements.append(Paragraph(f"Amount in words: {amount_to_words(payment_amount)}", normal_style))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(
        "This receipt confirms the payment above against the invoice referenced. "
        "It does not replace the original invoice.",
        normal_style
    ))
    elements.append(Spacer(1, 30))

    sig_style = styles["Normal"].clone("SigStyle")
    sig_style.alignment = TA_CENTER
    sig_style.fontSize = 10
    sig_style.fontName = "Helvetica-Bold"
    elements.append(Paragraph(f"For {company_name.upper()}", sig_style))
    elements.append(Spacer(1, 24))
    elements.append(Paragraph("Authorised Signatory", sig_style))

    doc.build(elements)
    return file_path