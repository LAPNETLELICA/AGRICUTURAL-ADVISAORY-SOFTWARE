from pathlib import Path

from integrations.cameroon_knowledge import CameroonKnowledgeProvider
from services.questionnaire import QuestionnaireService


def test_start_farming_without_passport_asks_previous_crop_and_usual_manure() -> None:
    service = QuestionnaireService(CameroonKnowledgeProvider(Path("BASE_CONNAISSANCES_AGRICOLES")))

    step = service.answer({"region": "West", "locality": "Bafoussam"}, "start_farming")

    assert step.key == "previous_crop"
    assert "manure" in step.prompt.lower()


def test_completion_builds_existing_mobile_advisory_request() -> None:
    service = QuestionnaireService(CameroonKnowledgeProvider(Path("BASE_CONNAISSANCES_AGRICOLES")))

    request = service.complete(
        {
            "farmer_id": "farmer-1",
            "crop_id": "tomato",
            "question": "How can I prepare my soil?",
            "region": "West",
            "locality": "Bafoussam",
            "usual_manure": "compost",
        }
    )

    assert request.crop_id == "tomato"
    assert request.evidence.practices["usual_manure"] == "compost"
