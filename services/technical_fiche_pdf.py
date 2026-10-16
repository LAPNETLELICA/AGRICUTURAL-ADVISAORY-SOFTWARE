"""Unicode PDF rendering for stored technical fiches."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    LongTable,
    PageTemplate,
    Paragraph,
    Spacer,
    TableStyle,
)

from services.technical_fiche import TechnicalFiche

_FONT_DIR = Path(__file__).resolve().parent / "assets" / "fonts"
_REGULAR_FONT = _FONT_DIR / "DejaVuSans.ttf"
_BOLD_FONT = _FONT_DIR / "DejaVuSans-Bold.ttf"
_FONT_NAME = "DejaVu"
_FONT_BOLD = "DejaVu-Bold"

_SECTION_ORDER = [
    "cover",
    "executive_summary",
    "farm_context",
    "diagnosis",
    "recommendations",
    "action_calendar",
    "monitoring",
    "safety",
    "references",
]

_LABELS: dict[str, dict[str, str]] = {
    "en": {
        "cover": "Cover",
        "executive_summary": "Summary",
        "farm_context": "Farm Context",
        "diagnosis": "Diagnosis",
        "recommendations": "Recommendations",
        "action_calendar": "Action Calendar",
        "monitoring": "Monitoring",
        "safety": "Safety",
        "references": "References",
    },
    "fr": {
        "cover": "Couverture",
        "executive_summary": "Résumé",
        "farm_context": "Contexte de l'exploitation",
        "diagnosis": "Diagnostic",
        "recommendations": "Recommandations",
        "action_calendar": "Calendrier des actions",
        "monitoring": "Suivi",
        "safety": "Sécurité",
        "references": "Références",
    },
}

_registered = False


def _register_fonts() -> None:
    global _registered
    if _registered:
        return
    if not _REGULAR_FONT.exists():
        raise RuntimeError("DejaVuSans.ttf font asset is missing")
    pdfmetrics.registerFont(TTFont(_FONT_NAME, str(_REGULAR_FONT)))
    bold_path = _BOLD_FONT if _BOLD_FONT.exists() else _REGULAR_FONT
    try:
        pdfmetrics.registerFont(TTFont(_FONT_BOLD, str(bold_path)))
    except Exception:
        globals()["_FONT_BOLD"] = _FONT_NAME
    _registered = True


def _language_of(fiche: TechnicalFiche) -> tuple[str, str | None]:
    content = fiche.content if isinstance(fiche.content, dict) else {}
    info = content.get("language")
    if isinstance(info, dict):
        raw = str(info.get("rendered", "en")).lower()
        rendered = "fr" if raw.startswith("fr") else "en"
        note = info.get("fallback_note")
        fallback = note.strip() if isinstance(note, str) and note.strip() else None
        return rendered, fallback
    return "en", None


def _stringify(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _header_footer(canvas, doc) -> None:  # type: ignore[no-untyped-def]
    canvas.saveState()
    canvas.setFont(_FONT_NAME, 8)
    canvas.setFillColor(colors.HexColor("#4b5563"))
    canvas.drawString(15 * mm, 282 * mm, "AGRIADVISE - Agricultural Technical File")
    canvas.drawRightString(195 * mm, 282 * mm, f"Page {doc.page}")
    canvas.drawCentredString(105 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _styles() -> dict[str, ParagraphStyle]:
    _register_fonts()
    base = getSampleStyleSheet()
    title = ParagraphStyle(
        "FicheTitle", parent=base["Title"], fontName=_FONT_BOLD,
        fontSize=18, leading=22, textColor=colors.HexColor("#111827"),
    )
    heading = ParagraphStyle(
        "FicheHeading", parent=base["Heading1"], fontName=_FONT_BOLD,
        fontSize=13, leading=16, textColor=colors.HexColor("#1f2937"),
        spaceBefore=10, spaceAfter=6,
    )
    sub = ParagraphStyle(
        "FicheSub", parent=base["Heading2"], fontName=_FONT_BOLD,
        fontSize=10, leading=13, textColor=colors.HexColor("#374151"),
        spaceBefore=6, spaceAfter=4,
    )
    normal = ParagraphStyle(
        "FicheNormal", parent=base["Normal"], fontName=_FONT_NAME,
        fontSize=9, leading=12.5, textColor=colors.HexColor("#111827"),
    )
    small = ParagraphStyle(
        "FicheSmall", parent=base["Normal"], fontName=_FONT_NAME,
        fontSize=8, leading=11, textColor=colors.HexColor("#374151"),
    )
    cell = ParagraphStyle(
        "FicheCell", parent=base["Normal"], fontName=_FONT_NAME,
        fontSize=8, leading=10.5, textColor=colors.HexColor("#111827"),
    )
    cell_h = ParagraphStyle(
        "FicheCellH", parent=cell, fontName=_FONT_BOLD, textColor=colors.white,
    )
    return {"title": title, "heading": heading, "sub": sub,
            "normal": normal, "small": small, "cell": cell, "cell_h": cell_h}


def _para(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(text, {'"': "&quot;"}), style)


def _dict_rows(data: dict, styles: dict[str, ParagraphStyle]) -> list:
    story: list = []
    for key, value in data.items():
        label = str(key).replace("_", " ").strip() or str(key)
        if isinstance(value, dict):
            story.append(_para(label.title(), styles["sub"]))
            story.extend(_dict_rows(value, styles))
        elif isinstance(value, list):
            story.append(_para(label.title(), styles["sub"]))
            if not value:
                story.append(_para("Not provided.", styles["normal"]))
            for item in value:
                if isinstance(item, dict):
                    story.extend(_dict_rows(item, styles))
                else:
                    text = _stringify(item).strip()
                    if text:
                        story.append(_para(f"- {text}", styles["normal"]))
        else:
            text = _stringify(value).strip()
            if text == "":
                continue
            story.append(_para(f"{label.title()}: {text}", styles["normal"]))
    return story


def _calendar_table(rows: list, styles: dict[str, ParagraphStyle], hdr: list[str]) -> LongTable:
    data: list[list[Paragraph]] = [[_para(c, styles["cell_h"]) for c in hdr]]
    for entry in rows:
        action = ""
        instr = ""
        period = ""
        mats = ""
        status = ""
        if isinstance(entry, dict):
            action = _stringify(entry.get("action")).strip()
            instr = _stringify(entry.get("instructions")).strip()
            period = _stringify(entry.get("period")).strip()
            status = _stringify(entry.get("status")).strip()
            raw_mats = entry.get("materials")
            if isinstance(raw_mats, list):
                mats = "; ".join(t for v in raw_mats if (t := _stringify(v).strip()))
            else:
                mats = _stringify(raw_mats).strip()
        else:
            action = _stringify(entry).strip()
            instr = action
        data.append([
            _para(action or "Not provided.", styles["cell"]),
            _para(instr or "Not provided.", styles["cell"]),
            _para(period or "Not provided.", styles["cell"]),
            _para(mats or "Not provided.", styles["cell"]),
            _para(status or "Not provided.", styles["cell"]),
        ])
    table = LongTable(
        data, colWidths=[38 * mm, 55 * mm, 28 * mm, 38 * mm, 26 * mm], repeatRows=1,
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#9ca3af")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table

def render_technical_fiche(fiche: TechnicalFiche) -> bytes:
    """Render a stored fiche as a Unicode-correct A4 PDF."""
    styles = _styles()
    content = fiche.content if isinstance(fiche.content, dict) else {}
    rendered, fallback = _language_of(fiche)
    labels = _LABELS["fr" if rendered == "fr" else "en"]
    sections = content.get("sections")
    if not isinstance(sections, list) or not sections:
        raise ValueError("fiche has no ordered sections to render")
    by_id: dict[str, object] = {}
    for item in sections:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            by_id[item["id"]] = item.get("fields")
    story: list = []
    story.append(_para("Agricultural Technical File", styles["title"]))
    story.append(Spacer(1, 4))
    if rendered == "fr":
        note = "Formulation agronomique conservee ; seuls les libelles sont localises."
    else:
        note = "Agronomic wording is retained; only section labels are localized."
    story.append(_para(note, styles["small"]))
    if fallback:
        story.append(Spacer(1, 2))
        story.append(_para(fallback, styles["small"]))
    story.append(Spacer(1, 2))
    story.append(_para(f"Language: {rendered}", styles["small"]))
    for sid in _SECTION_ORDER:
        fields = by_id.get(sid)
        if fields is None:
            fields = content.get(sid)
        if fields is None:
            continue
        story.append(KeepTogether([_para(labels.get(sid, sid), styles["heading"])]))
        if sid == "action_calendar" and isinstance(fields, list):
            if rendered == "fr":
                hdr = ["Action", "Instructions", "Periode", "Materiaux", "Statut"]
            else:
                hdr = ["Action", "Instructions", "Period", "Materials", "Status"]
            story.append(_calendar_table(fields, styles, hdr))
        elif isinstance(fields, dict):
            story.extend(_dict_rows(fields, styles))
        elif isinstance(fields, list):
            if not fields:
                story.append(_para("Not provided.", styles["normal"]))
            for item in fields:
                if isinstance(item, dict):
                    story.extend(_dict_rows(item, styles))
                else:
                    text = _stringify(item).strip()
                    if text:
                        story.append(_para(f"- {text}", styles["normal"]))
        else:
            text = _stringify(fields).strip()
            if text:
                story.append(_para(text, styles["normal"]))
        story.append(Spacer(1, 4))
    buf = BytesIO()
    doc = BaseDocTemplate(
        buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=20 * mm, bottomMargin=15 * mm,
        title="Agricultural Technical File", author="AGRIADVISE",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="fiche-frame")
    doc.addPageTemplates([PageTemplate(id="fiche-page", frames=[frame], onPage=_header_footer)])
    doc.build(story)
    pdf = buf.getvalue()
    if not pdf.startswith(b"%PDF-"):
        raise RuntimeError("PDF renderer produced invalid output")
    return pdf




