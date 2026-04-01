"""
PDF export: convert exam markdown to a downloadable PDF using ReportLab.
"""

import re
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def _strip_markdown_inline(text: str) -> str:
    """Remove **bold**, *italic*, `code` markers for plain PDF text."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    return text


def markdown_to_pdf(
    exam_markdown: str,
    answer_key_markdown: str | None = None,
    course: str = "",
    doc_type: str = "",
) -> bytes:
    """
    Convert exam markdown (and optional answer key) to PDF bytes.
    Returns the PDF as bytes ready to be sent as a file download.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    base = getSampleStyleSheet()

    styles = {
        "title": ParagraphStyle(
            "ExamTitle",
            parent=base["Title"],
            fontSize=18,
            spaceAfter=6,
            textColor=colors.HexColor("#1e293b"),
            alignment=TA_CENTER,
        ),
        "subtitle": ParagraphStyle(
            "ExamSubtitle",
            parent=base["Normal"],
            fontSize=11,
            spaceAfter=12,
            textColor=colors.HexColor("#475569"),
            alignment=TA_CENTER,
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontSize=14,
            spaceBefore=14,
            spaceAfter=4,
            textColor=colors.HexColor("#1e3a5f"),
            borderPad=4,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontSize=12,
            spaceBefore=10,
            spaceAfter=3,
            textColor=colors.HexColor("#334155"),
        ),
        "h3": ParagraphStyle(
            "H3",
            parent=base["Heading3"],
            fontSize=11,
            spaceBefore=8,
            spaceAfter=2,
            textColor=colors.HexColor("#475569"),
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontSize=10,
            leading=16,
            spaceAfter=4,
            textColor=colors.HexColor("#1e293b"),
        ),
        "option": ParagraphStyle(
            "Option",
            parent=base["Normal"],
            fontSize=10,
            leading=14,
            leftIndent=16,
            spaceAfter=2,
            textColor=colors.HexColor("#334155"),
        ),
        "code": ParagraphStyle(
            "Code",
            parent=base["Code"],
            fontSize=9,
            leading=13,
            leftIndent=12,
            fontName="Courier",
            backColor=colors.HexColor("#f1f5f9"),
            textColor=colors.HexColor("#1e293b"),
        ),
        "answer_label": ParagraphStyle(
            "AnswerLabel",
            parent=base["Normal"],
            fontSize=13,
            spaceBefore=16,
            spaceAfter=8,
            textColor=colors.HexColor("#166534"),
            fontName="Helvetica-Bold",
        ),
    }

    def parse_markdown_to_flowables(md: str, is_answer_key: bool = False) -> list:
        flowables = []
        lines = md.splitlines()
        in_code = False
        code_buffer = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Fenced code block
            if line.strip().startswith("```"):
                if in_code:
                    # End of code block
                    code_text = "<br/>".join(
                        l.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        for l in code_buffer
                    )
                    flowables.append(Paragraph(code_text or " ", styles["code"]))
                    flowables.append(Spacer(1, 4))
                    code_buffer = []
                    in_code = False
                else:
                    in_code = True
                i += 1
                continue

            if in_code:
                code_buffer.append(line)
                i += 1
                continue

            # Horizontal rule
            if re.match(r"^---+$", line.strip()):
                flowables.append(Spacer(1, 6))
                flowables.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1")))
                flowables.append(Spacer(1, 6))
                i += 1
                continue

            # Headings
            if line.startswith("### "):
                text = _strip_markdown_inline(line[4:].strip())
                flowables.append(Paragraph(text, styles["h3"]))
                i += 1
                continue
            if line.startswith("## "):
                text = _strip_markdown_inline(line[3:].strip())
                flowables.append(Paragraph(text, styles["h2"]))
                i += 1
                continue
            if line.startswith("# "):
                text = _strip_markdown_inline(line[2:].strip())
                if is_answer_key:
                    flowables.append(Paragraph(text, styles["answer_label"]))
                else:
                    flowables.append(Paragraph(text, styles["h1"]))
                i += 1
                continue

            # MCQ options (lines starting with A) B) C) D) or A. B. C. D.)
            if re.match(r"^[A-Da-d][).\s]", line.strip()):
                text = _strip_markdown_inline(line.strip())
                flowables.append(Paragraph(text, styles["option"]))
                i += 1
                continue

            # Numbered question or bullet
            if re.match(r"^\d+[.)]\s", line.strip()) or line.strip().startswith("- "):
                text = _strip_markdown_inline(line.strip())
                flowables.append(Paragraph(text, styles["body"]))
                i += 1
                continue

            # Blockquote
            if line.startswith("> "):
                text = _strip_markdown_inline(line[2:].strip())
                flowables.append(Paragraph(f"<i>{text}</i>", styles["option"]))
                i += 1
                continue

            # Empty line → small spacer
            if not line.strip():
                flowables.append(Spacer(1, 6))
                i += 1
                continue

            # Regular paragraph
            text = _strip_markdown_inline(line.strip())
            if text:
                flowables.append(Paragraph(text, styles["body"]))
            i += 1

        return flowables

    # ── Build document ─────────────────────────────────────────────────────────
    story = []

    # Cover header
    title = f"{course} — {doc_type.upper()}" if course and doc_type else "Exam"
    story.append(Paragraph(title, styles["title"]))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="80%", thickness=1, color=colors.HexColor("#4f46e5"), hAlign="CENTER"))
    story.append(Spacer(1, 16))

    # Exam content
    story.extend(parse_markdown_to_flowables(exam_markdown))

    # Answer key on a new page
    if answer_key_markdown:
        story.append(PageBreak())
        story.append(Paragraph("Answer Key", styles["answer_label"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#bbf7d0")))
        story.append(Spacer(1, 8))
        story.extend(parse_markdown_to_flowables(answer_key_markdown, is_answer_key=True))

    doc.build(story)
    return buffer.getvalue()