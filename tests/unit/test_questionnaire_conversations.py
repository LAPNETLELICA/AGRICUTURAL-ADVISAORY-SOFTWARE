from pathlib import Path

import pytest

from api.questionnaire import StartPayload
from engine.models.repositories import InMemoryConversationRepository
from integrations.cameroon_knowledge import CameroonKnowledgeProvider
from services.questionnaire import QuestionnaireService


def test_free_text_question_is_saved_and_requests_only_missing_onset() -> None:
    repository = InMemoryConversationRepository()
    service = QuestionnaireService(CameroonKnowledgeProvider(Path("BASE_CONNAISSANCES_AGRICOLES")), repository)
    started = service.start_conversation(farmer_id="farmer-1", region="West", locality="Bafoussam")

    result = service.receive_message(started.conversation.conversation_id, "My tomato leaves have yellow spots")

    assert result.step.key == "onset"
    assert result.conversation.context["crop_id"] == "tomato"
    assert [message.text for message in repository.list_messages(started.conversation.conversation_id)][-2:] == [
        "My tomato leaves have yellow spots",
        result.step.prompt,
    ]


def test_visible_start_farming_option_is_understood_as_question_intent() -> None:
    repository = InMemoryConversationRepository()
    service = QuestionnaireService(CameroonKnowledgeProvider(Path("BASE_CONNAISSANCES_AGRICOLES")), repository)
    started = service.start_conversation(farmer_id="farmer-1")

    result = service.receive_message(started.conversation.conversation_id, "Start farming")

    assert result.step.key == "crop"


def test_crop_answer_after_start_farming_advances_instead_of_repeating_crop() -> None:
    repository = InMemoryConversationRepository()
    service = QuestionnaireService(CameroonKnowledgeProvider(Path("BASE_CONNAISSANCES_AGRICOLES")), repository)
    started = service.start_conversation(farmer_id="farmer-1")

    intent = service.receive_message(started.conversation.conversation_id, "Start farming")
    crop = service.receive_message(intent.conversation.conversation_id, "Tomato")

    assert intent.step.key == "crop"
    assert crop.step.key != "crop"
    assert crop.conversation.context["crop_id"] == "tomato"


def test_questionnaire_options_expose_stable_ids_while_labels_remain_readable() -> None:
    repository = InMemoryConversationRepository()
    service = QuestionnaireService(CameroonKnowledgeProvider(Path("BASE_CONNAISSANCES_AGRICOLES")), repository)

    started = service.start_conversation(farmer_id="farmer-1")

    assert started.step.options[0].id == "start_farming"
    assert started.step.options[0].label == "Start farming"


def test_crop_problem_completes_after_onset_without_another_question() -> None:
    repository = InMemoryConversationRepository()
    service = QuestionnaireService(CameroonKnowledgeProvider(Path("BASE_CONNAISSANCES_AGRICOLES")), repository)
    started = service.start_conversation(farmer_id="farmer-1")

    onset = service.receive_message(
        started.conversation.conversation_id, "My tomato leaves have yellow spots"
    )
    completed = service.receive_message(
        onset.conversation.conversation_id, "Less than one week"
    )

    assert onset.step.key == "onset"
    assert completed.step is None
    assert completed.ready_request is not None


def test_start_conversation_preserves_language_for_the_contract() -> None:
    repository = InMemoryConversationRepository()
    service = QuestionnaireService(CameroonKnowledgeProvider(Path("BASE_CONNAISSANCES_AGRICOLES")), repository)

    started = service.start_conversation(farmer_id="farmer-1", language="fr")

    assert started.conversation.context["language"] == "fr"


def test_completed_conversation_rejects_a_stale_follow_up_answer() -> None:
    repository = InMemoryConversationRepository()
    service = QuestionnaireService(CameroonKnowledgeProvider(Path("BASE_CONNAISSANCES_AGRICOLES")), repository)
    started = service.start_conversation(farmer_id="farmer-1")
    onset = service.receive_message(
        started.conversation.conversation_id, "My tomato leaves have yellow spots"
    )
    service.receive_message(onset.conversation.conversation_id, "Less than one week")

    with pytest.raises(ValueError, match="already completed"):
        service.receive_message(started.conversation.conversation_id, "Tomato")


def test_questionnaire_start_payload_keeps_language() -> None:
    payload = StartPayload(farmer_id="farmer-1", language="fr")

    assert payload.language == "fr"


def test_french_soil_question_requests_location_before_crop_and_uses_known_context() -> None:
    repository = InMemoryConversationRepository()
    service = QuestionnaireService(CameroonKnowledgeProvider(Path("BASE_CONNAISSANCES_AGRICOLES")), repository)
    started = service.start_conversation(farmer_id="farmer-1", language="fr")

    location = service.receive_message(
        started.conversation.conversation_id, "Mon sol est pauvre et je veux le fertiliser"
    )
    concern = service.receive_message(location.conversation.conversation_id, "Bafoussam, West")

    assert location.step.key == "location"
    assert concern.step.key == "soil_concern"
    assert concern.conversation.context["locality"] == "Bafoussam"
    assert concern.step.key != "crop"
    assert "topography" in concern.step.known_context
