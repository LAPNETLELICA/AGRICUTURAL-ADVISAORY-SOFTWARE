from pathlib import Path

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
