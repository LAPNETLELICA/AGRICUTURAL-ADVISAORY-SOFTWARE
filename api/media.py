"""Authenticated controlled image-evidence endpoints."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import Response

from api.security import PrincipalDependency, enforce_owner
from services.media import MediaEvidence, MediaService

router = APIRouter(prefix="/api/v1/media", tags=["media"])


def _service(request: Request) -> MediaService:
    service: MediaService = request.app.state.media_service
    return service


def _public(item: MediaEvidence) -> dict[str, object]:
    return asdict(item)


@router.post("/images", status_code=status.HTTP_201_CREATED)
async def upload_image(
    request: Request,
    principal: PrincipalDependency,
    file: UploadFile = File(...),  # noqa: B008
    farmer_id: str = Form(...),
    crop_id: str | None = Form(None),
    request_id: str | None = Form(None),
) -> dict[str, object]:
    enforce_owner(principal, farmer_id)
    content = await file.read()
    item = _service(request).upload(
        farmer_id=farmer_id,
        crop_id=crop_id,
        request_id=request_id,
        content=content,
        mime_type=file.content_type or "",
        filename=file.filename,
    )
    request.app.state.audit_service.record(
        actor_id=principal.subject,
        action="media.upload",
        resource_type="image_evidence",
        resource_id=item.image_id,
        details={"crop_id": crop_id, "size_bytes": item.size_bytes},
    )
    return _public(item)


@router.get("/images/{image_id}")
def get_image(
    image_id: str,
    request: Request,
    principal: PrincipalDependency,
) -> Response:
    try:
        item, content = _service(request).get(image_id)
    except (KeyError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail="image evidence not found") from exc
    enforce_owner(principal, item.farmer_id)
    request.app.state.audit_service.record(
        actor_id=principal.subject,
        action="media.read",
        resource_type="image_evidence",
        resource_id=image_id,
    )
    return Response(
        content=content,
        media_type=item.mime_type,
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
            "Content-Disposition": f'inline; filename="{item.image_id}"',
        },
    )


@router.get("/images/{image_id}/metadata")
def image_metadata(
    image_id: str,
    request: Request,
    principal: PrincipalDependency,
) -> dict[str, object]:
    try:
        item = _service(request).metadata(image_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="image evidence not found") from exc
    enforce_owner(principal, item.farmer_id)
    return _public(item)


@router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(
    image_id: str,
    request: Request,
    principal: PrincipalDependency,
) -> Response:
    try:
        item = _service(request).metadata(image_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="image evidence not found") from exc
    enforce_owner(principal, item.farmer_id)
    _service(request).delete(image_id)
    request.app.state.audit_service.record(
        actor_id=principal.subject,
        action="media.delete",
        resource_type="image_evidence",
        resource_id=image_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
