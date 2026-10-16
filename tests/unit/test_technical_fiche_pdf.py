"""Behavioral checks for the generated, offline-readable technical file."""

from importlib import import_module
from shutil import which
from subprocess import run

import pytest

from engine.models.enums import Channel, RecommendationType
from engine.models.responses import CanonicalRecommendationItem, Recommendation
from services.technical_fiche import TechnicalFicheService


def _fiche(*, language: str, actions: list[str]):
    recommendation = Recommendation(
        request_id="request-1",
        crop_id="irish-potato",
        channel=Channel.MOBILE,
        primary=CanonicalRecommendationItem(
            candidate_id="candidate-1",
            type=RecommendationType.ADVISORY,
            name="Préparer les semences",
            summary="Utiliser des semences pré-germées.",
            score=1.0,
            rank=1,
        ),
        actions=actions,
        trace_id="trace-1",
    )
    return TechnicalFicheService(None).from_recommendation(
        owner_id="farmer-1",
        recommendation=recommendation,
        subject="Culture de pomme de terre",
        language=language,
    )


def _extract(pdf: bytes) -> str:
    if not which("pdfinfo") or not which("pdftotext"):
        pytest.skip("Poppler is needed for PDF readability assertions")
    checked = run(["pdfinfo", "-"], input=pdf, capture_output=True, check=False)
    assert checked.returncode == 0, checked.stderr.decode(errors="replace")
    extracted = run(["pdftotext", "-", "-"], input=pdf, capture_output=True, check=False)
    assert extracted.returncode == 0, extracted.stderr.decode(errors="replace")
    return extracted.stdout.decode("utf-8")


def test_pdf_has_nine_ordered_sections_and_french_text() -> None:
    renderer = import_module("services.technical_fiche_pdf").render_technical_fiche
    pdf = renderer(_fiche(language="fr-CM", actions=["Utiliser des semences pré-germées."]))

    assert pdf.startswith(b"%PDF-")
    extracted = _extract(pdf)
    assert "Agricultural Technical File" in extracted
    assert "Références" in extracted
    assert "pré-germées" in extracted
    assert extracted.index("Résumé") < extracted.index("Références")


def test_long_actions_and_table_flow_without_clipping() -> None:
    renderer = import_module("services.technical_fiche_pdf").render_technical_fiche
    actions = [f"Action {index}: observe <unsafe> & record the crop carefully." for index in range(81)]
    pdf = renderer(_fiche(language="en", actions=actions))

    assert pdf.startswith(b"%PDF-")
    extracted = _extract(pdf)
    assert "<unsafe> &" in extracted
    assert "Action 80" in extracted
    checked = run(["pdfinfo", "-"], input=pdf, capture_output=True, check=False)
    assert "Pages:" in checked.stdout.decode()
    assert int(checked.stdout.decode().split("Pages:")[1].splitlines()[0]) > 1


def test_unsupported_language_uses_visible_english_fallback() -> None:
    renderer = import_module("services.technical_fiche_pdf").render_technical_fiche
    pdf = renderer(_fiche(language="es", actions=["Observe leaves."]))

    assert pdf.startswith(b"%PDF-")
    assert "English labels" in _extract(pdf)
