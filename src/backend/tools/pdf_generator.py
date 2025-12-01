# src/backend/tools/pdf_generator.py

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from datetime import datetime

def generate_economic_report(filepath, country, indicators, analysis, rag_passages):
    """
    Simple PDF generator for economic analysis reports.
    """
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    title = f"Economic Intelligence Report – {country}"
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    story.append(Paragraph(title, styles["Title"]))
    story.append(Paragraph(f"Generated on {date_str}", styles["Normal"]))
    story.append(Spacer(1, 12))

    # Indicators
    story.append(Paragraph("<b>Indicators Analyzed:</b>", styles["Heading3"]))
    story.append(Paragraph(", ".join(indicators), styles["Normal"]))
    story.append(Spacer(1, 12))

    # Analysis
    story.append(Paragraph("<b>Economic Analysis:</b>", styles["Heading3"]))
    story.append(Paragraph(analysis.replace("\n", "<br/>"), styles["Normal"]))
    story.append(Spacer(1, 12))

    # RAG Context
    story.append(Paragraph("<b>Relevant Report Excerpts:</b>", styles["Heading3"]))
    if rag_passages.strip():
        for line in rag_passages.split("- "):
            if line.strip():
                story.append(Paragraph(f"• {line.strip()}", styles["Normal"]))
                story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("No RAG excerpts found.", styles["Normal"]))

    doc.build(story)

    return filepath
