"""Render repository Markdown and scientific PNGs with bundled ReportLab.

Use the bundled workspace Python; this is an offline publication renderer.
"""

import argparse
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def inline(text):
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r'<font name="Courier" size="8">\1</font>', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<link href="\2" color="#245581">\1</link>', text)
    return text


def render(source, output, *, anonymous=False):
    font_dir = Path(__file__).resolve().parents[1] / "completion_v12/final_package/fonts"
    for name, filename in [
        ("ACSerif", "DejaVuSerif.ttf"),
        ("ACSerif-Bold", "DejaVuSerif-Bold.ttf"),
        ("ACSerif-Italic", "DejaVuSerif-Italic.ttf"),
        ("ACSerif-BoldItalic", "DejaVuSerif-BoldItalic.ttf"),
        ("ACSans", "DejaVuSans.ttf"),
        ("ACSans-Bold", "DejaVuSans-Bold.ttf"),
    ]:
        pdfmetrics.registerFont(TTFont(name, str(font_dir / filename)))
    pdfmetrics.registerFontFamily(
        "ACSerif",
        normal="ACSerif",
        bold="ACSerif-Bold",
        italic="ACSerif-Italic",
        boldItalic="ACSerif-BoldItalic",
    )
    styles = getSampleStyleSheet()
    styles["Normal"].fontName = "ACSerif"
    styles["Normal"].fontSize = 10.5
    styles["Normal"].leading = 14
    styles["Normal"].spaceAfter = 7
    styles["Normal"].allowWidows = 0
    styles["Normal"].allowOrphans = 0
    for name, size, lead in [
        ("Title", 21, 25),
        ("Heading1", 14, 18),
        ("Heading2", 12, 15),
        ("Heading3", 11, 14),
    ]:
        styles[name].fontName = "ACSans-Bold"
        styles[name].fontSize = size
        styles[name].leading = lead
        styles[name].textColor = colors.HexColor("#18394d")
        styles[name].spaceBefore = 12
        styles[name].spaceAfter = 7
        if anonymous:
            styles[name].keepWithNext = True
    styles.add(
        ParagraphStyle(
            name="CaptionAC",
            fontName="ACSans",
            fontSize=8.5,
            leading=11,
            spaceAfter=10,
            textColor=colors.HexColor("#385166"),
        )
    )
    styles.add(ParagraphStyle(name="TableAC", fontName="ACSans", fontSize=8, leading=10))
    styles["Code"].fontSize = 7
    styles["Code"].leading = 9
    lines = source.read_text().splitlines()
    story = []
    buffer = []
    index = 0

    def flush():
        if buffer:
            story.append(Paragraph(inline(" ".join(buffer)), styles["Normal"]))
            buffer.clear()

    while index < len(lines):
        line = lines[index]
        index += 1
        if line.startswith("```"):
            flush()
            code = []
            while index < len(lines) and not lines[index].startswith("```"):
                code.append(lines[index])
                index += 1
            index += 1
            story.append(Preformatted("\n".join(code), styles["Code"], maxLineLength=95))
            continue
        if not line.strip():
            flush()
            continue
        m = re.match(r"^(#{1,4}) (.*)", line)
        if m:
            flush()
            level = len(m[1])
            style = "Title" if level == 1 else f"Heading{min(level - 1, 3)}"
            story.append(Paragraph(inline(m[2]), styles[style]))
            continue
        m = re.match(r"^!\[([^]]*)\]\(([^)]+)\)$", line)
        if m:
            flush()
            path = Path(m[2])
            path = path if path.is_absolute() else source.parent / path
            w, h = ImageReader(str(path)).getSize()
            width = 468
            story.append(Image(str(path), width=width, height=width * h / w))
            story.append(Paragraph(inline(m[1]), styles["CaptionAC"]))
            continue
        if line.startswith("|"):
            flush()
            tablelines = [line]
            while index < len(lines) and lines[index].startswith("|"):
                tablelines.append(lines[index])
                index += 1
            data = []
            for row in tablelines:
                cells = [s.strip() for s in row.strip("|").split("|")]
                if all(re.fullmatch(r"[-: ]+", c) for c in cells):
                    continue
                data.append([Paragraph(inline(c), styles["TableAC"]) for c in cells])
            if data:
                cols = len(data[0])
                table = Table(data, colWidths=[468 / cols] * cols, repeatRows=1, hAlign="LEFT")
                table.setStyle(
                    TableStyle(
                        [
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eff3")),
                            ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#6b8391")),
                            ("LINEBELOW", (0, 1), (-1, -1), 0.2, colors.HexColor("#d5dfe5")),
                            ("LEFTPADDING", (0, 0), (-1, -1), 5),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                            ("TOPPADDING", (0, 0), (-1, -1), 5),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ]
                    )
                )
                story.extend([table, Spacer(1, 9)])
            continue
        if line.startswith("- "):
            flush()
            story.append(Paragraph("&#8226; " + inline(line[2:]), styles["Normal"]))
            continue
        buffer.append(line)
    flush()
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output),
        pagesize=(612, 792),
        rightMargin=72,
        leftMargin=72,
        topMargin=53,
        bottomMargin=54,
        title=(
            source.read_text().splitlines()[0].lstrip("# ")
            if anonymous
            else source.stem.replace("_", " ")
        ),
        author="Anonymous" if anonymous else "AfterClick research artifact",
        pageCompression=1,
    )

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("ACSans", 8)
        canvas.setFillColor(colors.HexColor("#5b6c78"))
        canvas.drawString(
            72,
            31,
            "AfterClick | Anonymous empirical study"
            if anonymous
            else "AfterClick v12 | Evidence-grounded research artifact",
        )
        canvas.drawRightString(540, 31, str(doc.page))
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(output)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--anonymous", action="store_true")
    a = p.parse_args()
    render(a.source, a.output, anonymous=a.anonymous)
