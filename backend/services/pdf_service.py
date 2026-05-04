import io
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    PageBreak,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate, Frame

# ── Colours ──────────────────────────────────────────────────────────────────
DARK_NAVY = colors.HexColor("#0F1A2E")
MID_NAVY = colors.HexColor("#1A2F4E")
ACCENT_BLUE = colors.HexColor("#2563EB")
GOLD = colors.HexColor("#F59E0B")
SUCCESS_GREEN = colors.HexColor("#10B981")
HIGH_RISK_BG = colors.HexColor("#FEF2F2")
HIGH_RISK_BORDER = colors.HexColor("#EF4444")
MED_RISK_BG = colors.HexColor("#FFFBEB")
MED_RISK_BORDER = colors.HexColor("#F59E0B")
NOTE_BG = colors.HexColor("#EFF6FF")
NOTE_BORDER = colors.HexColor("#3B82F6")
GREY_LINE = colors.HexColor("#E2E8F0")
TEXT_DARK = colors.HexColor("#1E293B")
TEXT_GREY = colors.HexColor("#64748B")
WHITE = colors.white
BLACK = colors.black

PAGE_W, PAGE_H = A4


def _build_styles():
    styles = getSampleStyleSheet()

    cover_title = ParagraphStyle(
        "CoverTitle",
        fontName="Helvetica-Bold",
        fontSize=36,
        textColor=GOLD,
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    cover_sub = ParagraphStyle(
        "CoverSub",
        fontName="Helvetica",
        fontSize=14,
        textColor=WHITE,
        alignment=TA_CENTER,
        spaceAfter=20,
    )
    cover_doc_name = ParagraphStyle(
        "CoverDocName",
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=WHITE,
        alignment=TA_CENTER,
        leading=28,
        spaceAfter=8,
    )
    cover_doc_name_small = ParagraphStyle(
        "CoverDocNameSmall",
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=WHITE,
        alignment=TA_CENTER,
        leading=22,
        spaceAfter=8,
    )
    cover_meta = ParagraphStyle(
        "CoverMeta",
        fontName="Helvetica",
        fontSize=11,
        textColor=colors.HexColor("#94A3B8"),
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    cover_disclaimer = ParagraphStyle(
        "CoverDisclaimer",
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#94A3B8"),
        alignment=TA_CENTER,
        leading=13,
        spaceAfter=0,
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=DARK_NAVY,
        alignment=TA_LEFT,
        leftIndent=0,
        firstLineIndent=0,
        rightIndent=0,
        spaceBefore=10,
        spaceAfter=4,
    )
    body_text = ParagraphStyle(
        "BodyText2",
        fontName="Helvetica",
        fontSize=10,
        textColor=TEXT_DARK,
        leading=14,
        spaceAfter=4,
    )
    excerpt_text = ParagraphStyle(
        "ExcerptText",
        fontName="Helvetica-Oblique",
        fontSize=9,
        textColor=TEXT_GREY,
        leading=13,
        spaceAfter=4,
        leftIndent=8,
    )
    risk_title_style = ParagraphStyle(
        "RiskTitle",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=TEXT_DARK,
        spaceAfter=2,
    )
    risk_body_style = ParagraphStyle(
        "RiskBody",
        fontName="Helvetica",
        fontSize=9,
        textColor=TEXT_DARK,
        leading=13,
        spaceAfter=0,
    )
    page_heading = ParagraphStyle(
        "PageHeading",
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=DARK_NAVY,
        spaceAfter=8,
        spaceBefore=4,
    )
    label_style = ParagraphStyle(
        "LabelStyle",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=WHITE,
        alignment=TA_CENTER,
    )
    table_header_text = ParagraphStyle(
        "TableHeaderText",
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=WHITE,
        leading=14,
        spaceAfter=4,
    )

    return {
        "cover_title": cover_title,
        "cover_sub": cover_sub,
        "cover_doc_name": cover_doc_name,
        "cover_doc_name_small": cover_doc_name_small,
        "cover_meta": cover_meta,
        "cover_disclaimer": cover_disclaimer,
        "section_heading": section_heading,
        "body_text": body_text,
        "table_header_text": table_header_text,
        "excerpt_text": excerpt_text,
        "risk_title": risk_title_style,
        "risk_body": risk_body_style,
        "page_heading": page_heading,
        "label": label_style,
    }


SEVERITY_COLOURS = {
    "HIGH": (HIGH_RISK_BG, HIGH_RISK_BORDER, "#EF4444"),
    "MEDIUM": (MED_RISK_BG, MED_RISK_BORDER, "#F59E0B"),
    "NOTE": (NOTE_BG, NOTE_BORDER, "#3B82F6"),
}

CATEGORY_COLOURS = {
    "Your Rights": colors.HexColor("#10B981"),
    "Company Rights": colors.HexColor("#EF4444"),
    "Your Obligations": colors.HexColor("#F59E0B"),
    "Company Obligations": colors.HexColor("#6366F1"),
    "Termination": colors.HexColor("#EF4444"),
    "Liability & Disputes": colors.HexColor("#DC2626"),
    "Data & Privacy": colors.HexColor("#7C3AED"),
    "Payment & Fees": colors.HexColor("#D97706"),
    "Intellectual Property": colors.HexColor("#0891B2"),
    "Other": colors.HexColor("#64748B"),
}

RISK_LEVEL_COLOURS = {
    "LOW": SUCCESS_GREEN,
    "MEDIUM": colors.HexColor("#F59E0B"),
    "HIGH": colors.HexColor("#EF4444"),
}


class _NumberedCanvas:
    """Mixin for page numbering — handled via onFirstPage/onLaterPages."""
    pass


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(0.5)
    canvas.line(15 * mm, 12 * mm, PAGE_W - 15 * mm, 12 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(TEXT_GREY)
    canvas.drawString(15 * mm, 8 * mm, "LegalClear | Plain-English Legal Translation")
    canvas.drawRightString(
        PAGE_W - 15 * mm,
        8 * mm,
        f"Page {doc.page}",
    )
    canvas.restoreState()


def generate_pdf(translation_data: dict, document_name: str, original_filename: str = None) -> bytes:
    styles = _build_styles()
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=document_name,
        author="LegalClear",
        subject="Plain-English Legal Translation Report",
    )

    story = []
    now = datetime.now(timezone.utc)
    date_str = f"{now.day} {now.strftime('%B %Y')}"  # cross-platform, e.g. "3 May 2026"
    time_str = now.strftime("%H:%M UTC")

    # ── COVER PAGE ────────────────────────────────────────────────────────────
    # Spacer rows inside Tables don't set row height reliably in ReportLab;
    # use explicit TOPPADDING / BOTTOMPADDING per row instead.
    usable_w = PAGE_W - 30 * mm
    cover_bg_data = [
        [Paragraph("LegalClear", styles["cover_title"])],              # row 0
        [Paragraph("Legal Document Plain-English Translation Report",   # row 1
                   styles["cover_sub"])],
        # Adaptive font size: use smaller style for long names to prevent overflow
        [Paragraph(document_name,
                   styles["cover_doc_name"] if len(document_name) <= 40
                   else styles["cover_doc_name_small"])],                # row 2
        [Paragraph(f"Translated on: {date_str} at {time_str}",          # row 3
                   styles["cover_meta"])],
        [Paragraph(                                                       # row 4
            "This report was generated by LegalClear using AI analysis. "
            "It is provided for informational purposes only and does not "
            "constitute legal advice. If you have concerns about this "
            "document, consult a qualified legal professional.",
            styles["cover_disclaimer"],
        )],
    ]
    # If the user uploaded a file, insert an "Original Document" row before the disclaimer
    if original_filename:
        cover_bg_data.insert(4, [Paragraph(
            f"Original Document: {original_filename}",
            styles["cover_meta"],
        )])

    # None for row 2 = ReportLab auto-sizes to fit the content (handles long/wrapping names).
    # All other rows use fixed heights to prevent collapsing.
    cover_row_heights = [
        110,   # row 0: "LegalClear"
        50,    # row 1: subtitle
        None,  # row 2: document name — auto-height so long names never clip
        30,    # row 3: "Translated on"
        80,    # row 4: disclaimer (or original filename if present)
    ]
    if original_filename:
        cover_row_heights = [110, 50, None, 30, 36, 80]
    cover_table = Table(cover_bg_data, colWidths=[usable_w], rowHeights=cover_row_heights)
    cover_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND",   (0, 0), (-1, -1), DARK_NAVY),
                ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
                ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING",  (0, 0), (-1, -1), 20),
                ("RIGHTPADDING", (0, 0), (-1, -1), 20),
                ("TOPPADDING",   (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(cover_table)
    story.append(PageBreak())

    # ── EXECUTIVE SUMMARY ─────────────────────────────────────────────────────
    story.append(Paragraph("Executive Summary", styles["page_heading"]))
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=10))

    # Summary text
    story.append(Paragraph("<b>Document Summary</b>", styles["section_heading"]))
    story.append(Paragraph(translation_data.get("summary", ""), styles["body_text"]))
    story.append(Spacer(1, 8))

    # Parties table
    parties = translation_data.get("parties", [])
    if parties:
        story.append(Paragraph("<b>Parties Identified</b>", styles["section_heading"]))
        story.append(Spacer(1, 4))
        party_table_data = [
            [
                Paragraph("<b>Name</b>", styles["table_header_text"]),
                Paragraph("<b>Role</b>", styles["table_header_text"]),
                Paragraph("<b>Description</b>", styles["table_header_text"]),
            ]
        ]
        for p in parties:
            party_table_data.append(
                [
                    Paragraph(str(p.get("name", "")), styles["body_text"]),
                    Paragraph(str(p.get("role", "")), styles["body_text"]),
                    Paragraph(str(p.get("description", "")), styles["body_text"]),
                ]
            )
        pt = Table(party_table_data, colWidths=[40 * mm, 40 * mm, usable_w - 80 * mm])
        pt.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), MID_NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                    ("GRID", (0, 0), (-1, -1), 0.5, GREY_LINE),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, colors.HexColor("#F8FAFC")]),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(pt)
        story.append(Spacer(1, 10))

    # Stats
    story.append(Paragraph("<b>Analysis Statistics</b>", styles["section_heading"]))
    story.append(Spacer(1, 4))
    overall = translation_data.get("overall_risk_level", "LOW")
    overall_colour = RISK_LEVEL_COLOURS.get(overall, SUCCESS_GREEN)
    stats_data = [
        [
            Paragraph("<b>Metric</b>", styles["table_header_text"]),
            Paragraph("<b>Value</b>", styles["table_header_text"]),
        ],
        ["Total Sections Reviewed", str(translation_data.get("total_clauses_reviewed", 0))],
        ["High Risk Flags", str(translation_data.get("high_risk_count", 0))],
        ["Medium Risk Flags", str(translation_data.get("medium_risk_count", 0))],
        ["Notes", str(translation_data.get("note_count", 0))],
        ["Overall Risk Level", overall],
    ]
    st = Table(stats_data, colWidths=[100 * mm, usable_w - 100 * mm])
    st.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), MID_NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("GRID", (0, 0), (-1, -1), 0.5, GREY_LINE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, colors.HexColor("#F8FAFC")]),
                ("BACKGROUND", (1, -1), (1, -1), overall_colour),
                ("TEXTCOLOR", (1, -1), (1, -1), WHITE),
                ("FONTNAME", (1, -1), (1, -1), "Helvetica-Bold"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(st)
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(translation_data.get("overall_risk_explanation", ""), styles["body_text"])
    )
    story.append(PageBreak())

    # ── RISK SUMMARY ─────────────────────────────────────────────────────────
    story.append(Paragraph("Risk Summary", styles["page_heading"]))
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=10))

    sections = translation_data.get("sections", [])
    all_flags = []
    for sec in sections:
        for flag in sec.get("risk_flags", []):
            all_flags.append((sec.get("title", ""), flag))

    for severity_label, display_label in [("HIGH", "🔴 High Risk"), ("MEDIUM", "🟡 Medium Risk"), ("NOTE", "🔵 Notes")]:
        flags_for_level = [(t, f) for (t, f) in all_flags if f.get("severity") == severity_label]
        if not flags_for_level:
            continue
        display_text = {"HIGH": "HIGH RISK", "MEDIUM": "MEDIUM RISK", "NOTE": "NOTES"}.get(severity_label, display_label)
        story.append(Paragraph(f"<b>{display_text}</b>", styles["section_heading"]))
        bg_col, border_col, _ = SEVERITY_COLOURS.get(severity_label, (NOTE_BG, NOTE_BORDER, ""))
        for section_title, flag in flags_for_level:
            flag_data = [
                [
                    Paragraph(
                        f"<b>{flag.get('title', '')}</b> <font color='#64748B'>(from: {section_title})</font>",
                        styles["risk_title"],
                    )
                ],
                [Paragraph(flag.get("explanation", ""), styles["risk_body"])],
            ]
            ft = Table(flag_data, colWidths=[usable_w - 10])
            ft.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), bg_col),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, -1), (-1, -1), 5),
                        ("LINEBEFORE", (0, 0), (0, -1), 3, border_col),
                    ]
                )
            )
            story.append(ft)
            story.append(Spacer(1, 4))
        story.append(Spacer(1, 6))

    story.append(PageBreak())

    # ── FULL TRANSLATION ──────────────────────────────────────────────────────
    story.append(Paragraph("Full Translation", styles["page_heading"]))
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=10))

    for sec in sections:
        section_elements = []
        section_id = sec.get("section_id", "")
        title = sec.get("title", "")
        category = sec.get("category", "Other")
        cat_colour = CATEGORY_COLOURS.get(category, TEXT_GREY)

        # Section header row
        header_data = [
            [
                Paragraph(
                    f"<b>§{section_id} — {title}</b>",
                    styles["section_heading"],
                ),
                Paragraph(
                    f"<font color='white'><b> {category} </b></font>",
                    ParagraphStyle(
                        "CatBadge",
                        fontName="Helvetica-Bold",
                        fontSize=8,
                        textColor=WHITE,
                        alignment=TA_CENTER,
                    ),
                ),
            ]
        ]
        ht = Table(header_data, colWidths=[usable_w - 60 * mm, 60 * mm])
        ht.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BACKGROUND", (1, 0), (1, 0), cat_colour),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (1, 0), (1, 0), 4),
                    ("RIGHTPADDING", (1, 0), (1, 0), 4),
                ]
            )
        )
        section_elements.append(ht)

        # Original excerpt
        excerpt = sec.get("original_excerpt", "")
        if excerpt:
            section_elements.append(
                Paragraph(f'<i>"{excerpt}"</i>', styles["excerpt_text"])
            )

        # Plain English
        section_elements.append(
            Paragraph(sec.get("plain_english", ""), styles["body_text"])
        )

        # Risk flags
        for flag in sec.get("risk_flags", []):
            sev = flag.get("severity", "NOTE")
            bg_col, border_col, _ = SEVERITY_COLOURS.get(sev, (NOTE_BG, NOTE_BORDER, ""))
            sev_label = {"HIGH": "[HIGH RISK]", "MEDIUM": "[MEDIUM RISK]", "NOTE": "[NOTE]"}.get(
                sev, sev
            )
            flag_data = [
                [
                    Paragraph(
                        f"<b>{sev_label}: {flag.get('title', '')}</b>",
                        styles["risk_title"],
                    )
                ],
                [Paragraph(flag.get("explanation", ""), styles["risk_body"])],
            ]
            ft = Table(flag_data, colWidths=[usable_w - 10])
            ft.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), bg_col),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, -1), (-1, -1), 5),
                        ("LINEBEFORE", (0, 0), (0, -1), 3, border_col),
                    ]
                )
            )
            section_elements.append(ft)
            section_elements.append(Spacer(1, 3))

        section_elements.append(HRFlowable(width="100%", thickness=0.5, color=GREY_LINE, spaceAfter=4))
        section_elements.append(Spacer(1, 6))
        story.append(KeepTogether(section_elements))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    buffer.seek(0)
    return buffer.read()
