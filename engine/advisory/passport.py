"""On-demand V1 Crop Passport lifecycle management."""

from __future__ import annotations

from engine.interfaces.providers import CropPassportRepository
from engine.models.domain import CropPassport, utc_now
from engine.models.requests import AdvisoryRequest


class CropPassportService:
    def __init__(self, repository: CropPassportRepository) -> None:
        self._repository = repository

    def open_for_request(self, request: AdvisoryRequest) -> CropPassport | None:
        if request.crop_discovery or not request.farmer_id:
            return None

        passport = None
        if request.passport_id:
            passport = self._repository.get(request.passport_id)
            if passport is None:
                raise ValueError("passport was not found")
            if passport and (
                passport.farmer_id != request.farmer_id
                or passport.crop_id != request.crop_id
            ):
                raise ValueError("passport does not belong to this farmer and crop")
        if passport is None and not request.passport_id:
            passport = self._repository.find(
                request.farmer_id, request.crop_id, request.plot_ref
            )
        if passport is None:
            passport = CropPassport(
                farmer_id=request.farmer_id,
                crop_id=request.crop_id,
                plot_ref=request.plot_ref,
                current_stage=request.current_stage,
                stage_history=(
                    [{"stage": request.current_stage, "recorded_at": utc_now().isoformat()}]
                    if request.current_stage
                    else []
                ),
            )

        if request.current_stage and request.current_stage != passport.current_stage:
            history = [
                *passport.stage_history,
                {"stage": request.current_stage, "recorded_at": utc_now().isoformat()},
            ]
            passport = passport.model_copy(
                update={
                    "current_stage": request.current_stage,
                    "stage_history": history,
                    "updated_at": utc_now(),
                }
            )
        self._repository.save(passport)
        return passport

    def record_decision(
        self,
        passport_id: str | None,
        recommendation_id: str,
        trace_id: str,
    ) -> None:
        if not passport_id:
            return
        passport = self._repository.get(passport_id)
        if passport is None:
            return
        updated = passport.model_copy(
            update={
                "recommendation_ids": [*passport.recommendation_ids, recommendation_id],
                "trace_ids": [*passport.trace_ids, trace_id],
                "updated_at": utc_now(),
            }
        )
        self._repository.save(updated)
