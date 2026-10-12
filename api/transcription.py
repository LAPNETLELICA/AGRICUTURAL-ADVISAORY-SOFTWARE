"""Authenticated voice-input endpoint backed by the configured transcription provider."""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel

from api.security import PrincipalDependency
from engine.exceptions import ProviderUnavailableError

router = APIRouter(prefix="/api/v1/advisory", tags=["voice"])

_MAX_AUDIO_BYTES = 25 * 1024 * 1024


class TranscriptionResponse(BaseModel):
    text: str
    language: str | None = None


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_voice(
    request: Request,
    principal: PrincipalDependency,
    file: UploadFile = File(...),  # noqa: B008
    language: str | None = Form(None),
) -> TranscriptionResponse:
    """Turn a farmer's audio recording into text without persisting the audio."""
    del principal
    mime_type = file.content_type or "application/octet-stream"
    if not (mime_type.startswith("audio/") or mime_type in {"application/ogg", "video/webm"}):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="audio file required"
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="audio file is empty")
    if len(content) > _MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="audio file exceeds the 25 MiB transcription limit",
        )

    try:
        text = request.app.state.container.transcription.transcribe(
            content,
            filename=file.filename or "voice-recording",
            mime_type=mime_type,
            language=language,
        )
    except (ProviderUnavailableError, TimeoutError, ConnectionError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return TranscriptionResponse(text=text, language=language)
