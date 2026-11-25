"""Format the unified Markdown as a venue-neutral PDF with the bundled reportlab runtime."""

import argparse
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[2]


def inline(text):
    text = text.translate(
        str.maketrans(
            {"→": " to ", "–": "-", "—": " - ", "−": "-", "×": " x ", "≤": "<=", "≥": ">="}
        )
    )
    text = html.escape(text)
    text = re.sub(
        r"\[([^]]+)\]\((https?://[^)]+)\)", r'<link href="\2" color="#245b70">\1</link>', text
    )
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)
    return text.replace("`", "")


def render(source, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="BodyPaper",
            fontName="Times-Roman",
            fontSize=10,
            leading=12.8,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
        )
    )
    styles.add(
        ParagraphStyle(
            name="PaperTitle",
            fontName="Times-Bold",
            fontSize=20,
            leading=23,
            alignment=TA_CENTER,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="PaperSubtitle",
            fontName="Times-Italic",
            fontSize=11,
            leading=14,
            alignment=TA_CENTER,
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(name="Cell", fontName="Times-Roman", fontSize=8, leading=10, wordWrap="CJK")
    )
    styles["Heading1"].fontName = "Times-Bold"
    styles["Heading1"].fontSize = 13
    styles["Heading1"].leading = 16
    styles["Heading2"].fontName = "Times-Bold"
    styles["Heading2"].fontSize = 11
    styles["Heading2"].leading = 13
    story = []
    lines = source.read_text().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("```"):
            i += 1
            code = []
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            for c in code:
                story.append(Paragraph(html.escape(c), styles["Cell"]))
            story.append(Spacer(1, 7))
            i += 1
            continue
        if line.startswith("!["):
            m = re.match(r"!\[([^]]*)\]\(([^)]+)\)", line)
            p = source.parent / m[2]
            w, h = ImageReader(str(p)).getSize()
            width = 460
            height = width * h / w
            if height > 235:
                width *= 235 / height
                height = 235
            image = Image(str(p), width=width, height=height)
            image.keepWithNext = True
            gap = Spacer(1, 6)
            gap.keepWithNext = True
            story.extend([image, gap])
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [x.strip() for x in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"[:\- ]+", x) for x in cells):
                    rows.append([Paragraph(inline(x), styles["Cell"]) for x in cells])
                i += 1
            n = len(rows[0])
            widths = [468 / n] * n
            t = Table(rows, colWidths=widths, repeatRows=1, hAlign="CENTER")
            t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef1")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LINEBELOW", (0, 0), (-1, 0), 0.7, colors.HexColor("#486775")),
                        ("LINEBELOW", (0, -1), (-1, -1), 0.4, colors.HexColor("#486775")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            story.append(KeepTogether([t, Spacer(1, 9)]))
            continue
        if line.startswith("# "):
            style = styles["PaperTitle"]
            value = line[2:]
        elif line.startswith("### "):
            style = styles["Heading2"]
            value = line[4:]
        elif line.startswith("## "):
            style = styles["Heading1"]
            value = line[3:]
        elif line.startswith("*An Empirical"):
            style = styles["PaperSubtitle"]
            value = line
        else:
            style = styles["BodyPaper"]
            value = line
            while (
                i + 1 < len(lines)
                and lines[i + 1].strip()
                and not lines[i + 1].startswith(("#", "|", "![", "```"))
            ):
                i += 1
                value += " " + lines[i].strip()
        story.append(Paragraph(inline(value), style))
        i += 1

    def footer(canvas, doc):
        canvas.setFont("Times-Roman", 8)
        canvas.setFillColor(colors.HexColor("#555555"))
        canvas.drawString(54, 32, "AfterClick | Bounded empirical manuscript | 24 November 2026")
        canvas.drawRightString(558, 32, str(doc.page))

    SimpleDocTemplate(
        str(output),
        pagesize=(612, 792),
        rightMargin=54,
        leftMargin=54,
        topMargin=45,
        bottomMargin=49,
        title="AfterClick: The Limits of Recoverability in Tool-Using LLM Agents",
        author="AfterClick research artifact",
    ).build(story, onFirstPage=footer, onLaterPages=footer)
    print(output)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument(
        "--output", type=Path, default=ROOT / "output/pdf/AFTERCLICK_RECOVERABILITY_PAPER.pdf"
    )
    a = p.parse_args()
    render(ROOT / "paper/AFTERCLICK_RECOVERABILITY_PAPER.md", a.output)
