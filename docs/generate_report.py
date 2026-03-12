from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
SOURCE = DOCS_DIR / "final_technical_report.md"
OUTPUT = DOCS_DIR / "final_technical_report.pdf"
LOGO = ROOT / "static" / "images" / "logo.png"
SCREENSHOTS_DIR = DOCS_DIR / "screenshots"


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleCenter",
            parent=styles["Title"],
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1f2937"),
            spaceAfter=18,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading2"],
            textColor=colors.HexColor("#111827"),
            spaceBefore=10,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyTight",
            parent=styles["BodyText"],
            leading=15,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BulletTight",
            parent=styles["BodyText"],
            leftIndent=16,
            bulletIndent=6,
            leading=15,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Caption",
            parent=styles["Italic"],
            alignment=TA_CENTER,
            textColor=colors.HexColor("#4b5563"),
            spaceAfter=10,
        )
    )
    return styles


def add_logo(story):
    if not LOGO.exists():
        return
    image = Image(str(LOGO))
    image.drawHeight = 55
    image.drawWidth = 55
    image.hAlign = "CENTER"
    story.append(image)
    story.append(Spacer(1, 10))


def safe_text(line: str) -> str:
    return line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def add_markdown_body(story, styles):
    first_title = True
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    for raw in lines:
        line = raw.strip()
        if not line:
            story.append(Spacer(1, 6))
            continue
        if line.startswith("# "):
            text = safe_text(line[2:].strip())
            style = "TitleCenter" if first_title else "Section"
            first_title = False
            story.append(Paragraph(text, styles[style]))
        elif line.startswith("## "):
            story.append(Paragraph(safe_text(line[3:].strip()), styles["Section"]))
        elif line.startswith("### "):
            story.append(Paragraph(safe_text(line[4:].strip()), styles["Heading3"]))
        elif line.startswith("- "):
            story.append(Paragraph(safe_text(line[2:].strip()), styles["BulletTight"], bulletText="-"))
        else:
            story.append(Paragraph(safe_text(line), styles["BodyTight"]))


def fit_image(path: Path, max_width: float = 460, max_height: float = 300):
    reader = ImageReader(str(path))
    width, height = reader.getSize()
    scale = min(max_width / width, max_height / height, 1)
    image = Image(str(path), width=width * scale, height=height * scale)
    image.hAlign = "CENTER"
    return image


def add_screenshots(story, styles):
    if not SCREENSHOTS_DIR.exists():
        return
    image_files = []
    for pattern in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
        image_files.extend(sorted(SCREENSHOTS_DIR.glob(pattern)))
    if not image_files:
        return

    story.append(Spacer(1, 8))
    story.append(Paragraph("Embedded Website Screenshots", styles["Section"]))
    for image_path in image_files:
        story.append(fit_image(image_path))
        caption = image_path.stem.replace("_", " ").replace("-", " ").title()
        story.append(Spacer(1, 6))
        story.append(Paragraph(caption, styles["Caption"]))


def add_page_number(canvas, doc):
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(A4[0] - 48, 24, f"Page {doc.page}")


def main():
    DOCS_DIR.mkdir(exist_ok=True)
    SCREENSHOTS_DIR.mkdir(exist_ok=True)
    styles = build_styles()
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=48,
        leftMargin=48,
        topMargin=48,
        bottomMargin=48,
    )
    story = []
    add_logo(story)
    add_markdown_body(story, styles)
    add_screenshots(story, styles)
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(OUTPUT)


if __name__ == "__main__":
    main()
