"""Provider-neutral voice preparation endpoint.

Voice stays an explicit text fallback until a real TTS adapter is configured.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from api.dependencies import ContainerDependency
from api.security import PrincipalDependency, enforce_owner
from engine.exceptions import ProviderUnavailableError
from engine.models.requests import AdvisoryRequest, MobileAdvisoryRequest

router = APIRouter(prefix="/api/v1/advisory", tags=["voice"])


class VoiceResponse(BaseModel):
    text: str
    language: str
    audio_available: bool
    audio_media_type: str | None = None
    audio_base64: str | None = None
    fallback_reason: str | None = None


@router.post("/voice", response_model=VoiceResponse)
def voice_advisory(
    request: MobileAdvisoryRequest,
    http_request: Request,
    container: ContainerDependency,
    principal: PrincipalDependency,
) -> VoiceResponse:
    import base64

    enforce_owner(principal, request.farmer_id)
    try:
        http_request.app.state.media_service.validate_references(
            request.farmer_id, request.evidence.image_references
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    recommendation = container.engine.advise(AdvisoryRequest.from_mobile(request))
    text = container.voice_formatter.format(recommendation)
    if request.language.lower() != "en":
        text = container.translator.translate(text, request.language)
    try:
        audio = container.speech.synthesize(text, request.language)
    except (ProviderUnavailableError, TimeoutError, ConnectionError) as exc:
        return VoiceResponse(
            text=text,
            language=request.language,
            audio_available=False,
            fallback_reason=str(exc),
        )
    return VoiceResponse(
        text=text,
        language=request.language,
        audio_available=True,
        audio_media_type="audio/mpeg",
        audio_base64=base64.b64encode(audio).decode("ascii"),
    )
