from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import io
import re

# ── Colour palette ───────────────────────────────────
PRIMARY  = colors.HexColor("#1E3A5F")
ACCENT   = colors.HexColor("#2E86AB")
SUCCESS  = colors.HexColor("#27AE60")
WARNING  = colors.HexColor("#E67E22")
DANGER   = colors.HexColor("#E74C3C")
LIGHT_BG = colors.HexColor("#F0F4F8")
WHITE    = colors.white
TEXT     = colors.HexColor("#2C3E50")
GREY     = colors.HexColor("#7F8C8D")


def _styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("DocTitle",  fontName="Helvetica-Bold", fontSize=24,
                         textColor=PRIMARY, leading=30, spaceAfter=8))
    s.add(ParagraphStyle("DocSub",    fontName="Helvetica",      fontSize=11,
                         textColor=ACCENT,  leading=15, spaceBefore=2, spaceAfter=8))
    s.add(ParagraphStyle("SecHeader", fontName="Helvetica-Bold", fontSize=13,
                         textColor=WHITE,   leading=16, spaceAfter=2))
    s.add(ParagraphStyle("SubHeader", fontName="Helvetica-Bold", fontSize=11,
                         textColor=PRIMARY, leading=14, spaceBefore=6, spaceAfter=4))
    s.add(ParagraphStyle("BodyText2", fontName="Helvetica",      fontSize=9,
                         textColor=TEXT,    leading=16, spaceAfter=6))
    s.add(ParagraphStyle("SmallGrey", fontName="Helvetica",      fontSize=8,
                         textColor=GREY,    leading=12, spaceAfter=2))
    return s


def _section_header(title, story, styles):
    story.append(Spacer(1, 18))
    tbl = Table([[Paragraph(f"  {title}", styles["SecHeader"])]], colWidths=[6.5 * inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), PRIMARY),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 8))


def _score_box(score, story):
    colour = SUCCESS if score >= 70 else (WARNING if score >= 45 else DANGER)
    label  = ("Excellent" if score >= 80 else
              "Good"      if score >= 60 else
              "Fair"      if score >= 45 else "Needs Work")

    score_para = Paragraph(str(score), ParagraphStyle(
        "SN2", fontName="Helvetica-Bold", fontSize=42, leading=50,
        textColor=colour, alignment=1, spaceAfter=4))
    label_para = Paragraph(f"{label} ATS Score", ParagraphStyle(
        "LB", fontName="Helvetica-Bold", fontSize=11, leading=14,
        textColor=colour, alignment=1, spaceBefore=2, spaceAfter=2))
    out_para = Paragraph("out of 100", ParagraphStyle(
        "OO", fontName="Helvetica", fontSize=9, leading=12,
        textColor=TEXT, alignment=1))

    tbl = Table([[score_para], [label_para], [out_para]], colWidths=[2.5 * inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHT_BG),
        ("TOPPADDING",    (0, 0), (0, 0),   14),
        ("BOTTOMPADDING", (0, 0), (0, 0),   2),
        ("TOPPADDING",    (0, 1), (0, 1),   0),
        ("BOTTOMPADDING", (0, 1), (0, 1),   2),
        ("TOPPADDING",    (0, 2), (0, 2),   0),
        ("BOTTOMPADDING", (0, 2), (0, 2),   14),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
    ]))
    wrapper = Table([[tbl]], colWidths=[6.5 * inch])
    wrapper.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    story.append(wrapper)
    story.append(Spacer(1, 10))


def _kw_chips(keywords, story, colour):
    """Render keywords as coloured chip-style table cells."""
    if not keywords:
        return
    chip_style = ParagraphStyle("Chip", fontName="Helvetica-Bold",
                                fontSize=8, textColor=WHITE, alignment=1)
    row, rows = [], []
    for i, kw in enumerate(keywords):
        row.append(Paragraph(kw, chip_style))
        if len(row) == 4 or i == len(keywords) - 1:
            while len(row) < 4:
                row.append("")
            rows.append(row)
            row = []

    tbl = Table(rows, colWidths=[1.55 * inch] * 4)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colour),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 10))


def _highlight_keywords(text: str, matched: list, missing: list) -> str:
    """
    Wrap matched keywords in blue bold tags and missing keywords in red bold tags
    for ReportLab XML markup. Case-insensitive, whole-word matching.
    """
    if not text:
        return text

    # Build combined list: matched first (blue), missing (red)
    # Longer keywords processed first to avoid partial matches
    all_kw = sorted(
        [(kw, "matched") for kw in matched] +
        [(kw, "missing") for kw in missing],
        key=lambda x: len(x[0]),
        reverse=True
    )

    for kw, kw_type in all_kw:
        if not kw.strip():
            continue
        escaped = re.escape(kw)
        if kw_type == "matched":
            replacement = f'<font color="#2E86AB"><b>{kw}</b></font>'
        else:
            replacement = f'<font color="#E74C3C"><b>{kw}</b></font>'

        text = re.sub(
            rf'\b({escaped})\b',
            replacement,
            text,
            flags=re.IGNORECASE
        )
    return text


def generate_pdf_report(candidate_name, score_data, jd_match=None, interview_questions=None):
    """Build and return a branded PDF report as bytes."""

    # Extract keyword lists for highlighting
    matched_kw = []
    missing_kw = []
    if jd_match:
        matched_kw = jd_match.get("matched_keywords", [])
        missing_kw = jd_match.get("missing_keywords", [])

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch
    )
    styles = _styles()
    story  = []

    # ── Title block ─────────────────────────────────
    story.append(Paragraph("SmartResume AI", styles["DocTitle"]))
    story.append(Paragraph(
        f"Analysis Report — {candidate_name or 'Candidate'}",
        styles["DocSub"]))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=14))

    # ── ATS Score ───────────────────────────────────
    _section_header("ATS Resume Score", story, styles)
    score = int(score_data.get("score", 0) or 0)
    _score_box(score, story)

    verdict_text = score_data.get("verdict", "")
    if matched_kw or missing_kw:
        verdict_text = _highlight_keywords(verdict_text, matched_kw, missing_kw)
    story.append(Paragraph(verdict_text, styles["BodyText2"]))
    story.append(Spacer(1, 14))

    # ── Strengths ───────────────────────────────────
    if score_data.get("strengths"):
        _section_header("Strengths", story, styles)
        for item in score_data["strengths"]:
            highlighted = _highlight_keywords(item, matched_kw, missing_kw)
            story.append(Paragraph(f"+  {highlighted}", ParagraphStyle(
                "Str", fontName="Helvetica", fontSize=9, leading=15,
                leftIndent=12, textColor=SUCCESS, spaceAfter=6)))

    # ── Areas for Improvement ───────────────────────
    if score_data.get("weaknesses"):
        _section_header("Areas for Improvement", story, styles)
        for item in score_data["weaknesses"]:
            highlighted = _highlight_keywords(item, matched_kw, missing_kw)
            story.append(Paragraph(f"!  {highlighted}", ParagraphStyle(
                "Wk", fontName="Helvetica", fontSize=9, leading=15,
                leftIndent=12, textColor=WARNING, spaceAfter=6)))

    # ── JD Match ────────────────────────────────────
    if jd_match:
        _section_header("Job Description Match", story, styles)
        ms       = int(jd_match.get("match_score", 0) or 0)
        ms_color = SUCCESS if ms >= 70 else (WARNING if ms >= 45 else DANGER)
        ms_label = "Strong Match" if ms >= 70 else ("Partial Match" if ms >= 45 else "Weak Match")

        # Match score display
        ms_para = Paragraph(f"{ms}%", ParagraphStyle(
            "MS", fontName="Helvetica-Bold", fontSize=28, leading=34,
            textColor=ms_color, alignment=1))
        ml_para = Paragraph(ms_label, ParagraphStyle(
            "ML", fontName="Helvetica-Bold", fontSize=10, leading=13,
            textColor=ms_color, alignment=1))
        ms_tbl = Table([[ms_para], [ml_para]], colWidths=[2.0 * inch])
        ms_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), LIGHT_BG),
            ("TOPPADDING",    (0, 0), (0, 0),   10),
            ("BOTTOMPADDING", (0, 0), (0, 0),   2),
            ("TOPPADDING",    (0, 1), (0, 1),   0),
            ("BOTTOMPADDING", (0, 1), (0, 1),   10),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ]))
        wrap = Table([[ms_tbl]], colWidths=[6.5 * inch])
        wrap.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
        story.append(wrap)
        story.append(Spacer(1, 10))

        verdict = _highlight_keywords(
            jd_match.get("match_verdict", ""), matched_kw, missing_kw)
        story.append(Paragraph(verdict, styles["BodyText2"]))

        if matched_kw:
            story.append(Paragraph("Matched Keywords", styles["SubHeader"]))
            _kw_chips(matched_kw, story, SUCCESS)

        if missing_kw:
            story.append(Paragraph("Missing Keywords", styles["SubHeader"]))
            _kw_chips(missing_kw, story, DANGER)

        if jd_match.get("recommended_keywords"):
            story.append(Paragraph("Recommended Keywords to Add", styles["SubHeader"]))
            _kw_chips(jd_match["recommended_keywords"], story, ACCENT)

    # ── Interview Questions ──────────────────────────
    if interview_questions:
        _section_header("Interview Questions", story, styles)
        type_colours = {
            "Technical":     ACCENT,
            "Behavioral":    SUCCESS,
            "Project-Based": PRIMARY,
            "Situational":   WARNING,
        }
        for q in interview_questions:
            qtype  = q.get("type",     "General")
            qnum   = q.get("number",   "")
            qtext  = q.get("question", "")
            colour = type_colours.get(qtype, TEXT)

            # Highlight keywords in questions too
            qtext_hl = _highlight_keywords(qtext, matched_kw, missing_kw)

            tag = Paragraph(f"[{qtype}]", ParagraphStyle(
                "QTag", fontName="Helvetica-Bold", fontSize=8, textColor=colour))
            qtxt_p = Paragraph(f"<b>Q{qnum}.</b> {qtext_hl}", ParagraphStyle(
                "QTxt", fontName="Helvetica", fontSize=9, leading=14, textColor=TEXT))

            row_tbl = Table([[tag, qtxt_p]], colWidths=[1.1 * inch, 5.4 * inch])
            row_tbl.setStyle(TableStyle([
                ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING",    (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING",   (0, 0), (-1, -1), 2),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
            ]))
            story.append(row_tbl)
            story.append(Spacer(1, 4))
            story.append(HRFlowable(width="100%", thickness=0.5,
                                    color=colors.HexColor("#D0D8E0"), spaceAfter=8))

    doc.build(story)
    buf.seek(0)
    return buf.read()