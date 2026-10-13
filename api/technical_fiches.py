"""Private authoring and public reading of sanitized technical fiches."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import Field

from api.security import AdminDependency, PrincipalDependency
from engine.models.domain import StrictModel

router = APIRouter(prefix="/api/v1/technical-fiches", tags=["technical fiches"])


def _pdf_document(lines: list[str]) -> bytes:
    """Create a small dependency-free PDF from already-sanitized text."""

    def escape(line: str) -> str:
        return (
            line.encode("latin-1", "replace")
            .decode("latin-1")
            .replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
        )

    commands = [f"({escape(line)[:110]}) Tj 0 -16 Td" for line in lines]
    content = "BT /F1 11 Tf 50 780 Td " + " ".join(commands) + " ET"
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            "/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(content.encode('latin-1'))} >>\nstream\n{content}\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n{obj}\nendobj\n".encode("latin-1"))
    start = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    output.extend("".join(f"{offset:010} 00000 n \n" for offset in offsets[1:]).encode())
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF".encode()
    )
    return bytes(output)


class FicheCreate(StrictModel):
    recommendation_id: str = Field(min_length=1, max_length=100)
    subject: str = Field(min_length=1, max_length=100)
    language: str = Field(default="en", min_length=2, max_length=20)


class FicheStatus(StrictModel):
    status: str


@router.post("")
def create_fiche(
    payload: FicheCreate, request: Request, principal: PrincipalDependency
) -> dict[str, object]:
    recommendation = request.app.state.container.recommendations.get(payload.recommendation_id)
    if recommendation is None:
        raise HTTPException(status_code=404, detail="recommendation not found")
    trace = request.app.state.container.traces.get(recommendation.trace_id)
    farmer_id = trace.context_used.get("farmer_id") if trace else None
    if not principal.is_admin and farmer_id != principal.subject:
        raise HTTPException(status_code=403, detail="recommendation ownership required")
    fiche = request.app.state.technical_fiche_service.from_recommendation(
        owner_id=principal.subject,
        recommendation=recommendation,
        subject=payload.subject,
        language=payload.language,
    )
    return asdict(fiche)


@router.get("")
def public_fiches(
    request: Request,
    principal: PrincipalDependency,
    crop_id: str | None = None,
    subject: str | None = None,
) -> list[dict[str, object]]:
    del principal
    return [
        asdict(item)
        for item in request.app.state.technical_fiche_service.list_published(
            crop_id=crop_id, subject=subject
        )
    ]


@router.get("/{fiche_id}")
def read_fiche(
    fiche_id: str, request: Request, principal: PrincipalDependency
) -> dict[str, object]:
    del principal
    fiche = request.app.state.technical_fiche_service.get(fiche_id)
    if fiche is None or fiche.status != "PUBLISHED":
        raise HTTPException(status_code=404, detail="technical fiche not found")
    return asdict(fiche)


@router.put("/{fiche_id}/status")
def update_fiche_status(
    fiche_id: str, payload: FicheStatus, request: Request, admin: AdminDependency
) -> dict[str, object]:
    del admin
    try:
        return asdict(
            request.app.state.technical_fiche_service.set_status(fiche_id, payload.status)
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="technical fiche not found") from exc


@router.get("/{fiche_id}/download")
def download_fiche(fiche_id: str, request: Request, principal: PrincipalDependency) -> Response:
    fiche = read_fiche(fiche_id, request, principal)
    lines = ["AGRIADVISE technical fiche"]
    lines.extend(f"{key}: {value}" for key, value in fiche["content"].items())
    return Response(
        _pdf_document(lines),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="fiche-{fiche_id}.pdf"'},
    )
