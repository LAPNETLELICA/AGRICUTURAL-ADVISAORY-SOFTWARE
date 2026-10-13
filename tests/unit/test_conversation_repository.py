from engine.models.conversations import AdvisoryConversation, ConversationMessage, ConversationStatus
from engine.models.repositories import InMemoryConversationRepository


def test_repository_keeps_conversation_messages_separate_and_ordered() -> None:
    repository = InMemoryConversationRepository()
    first = AdvisoryConversation.create("farmer-1")
    second = AdvisoryConversation.create("farmer-1")
    repository.create(first)
    repository.create(second)

    repository.append_message(first.conversation_id, ConversationMessage.farmer(1, "Tomato leaves yellow"))
    repository.append_message(second.conversation_id, ConversationMessage.farmer(1, "When plant maize?"))
    repository.append_message(first.conversation_id, ConversationMessage.assistant(2, "When did it start?"))

    assert [item.text for item in repository.list_messages(first.conversation_id)] == [
        "Tomato leaves yellow",
        "When did it start?",
    ]
    assert [item.text for item in repository.list_messages(second.conversation_id)] == [
        "When plant maize?",
    ]


def test_repository_returns_latest_open_conversation_only() -> None:
    repository = InMemoryConversationRepository()
    completed = AdvisoryConversation.create("farmer-1")
    completed.status = ConversationStatus.COMPLETED
    active = AdvisoryConversation.create("farmer-1")
    repository.create(completed)
    repository.create(active)

    assert repository.latest_open("farmer-1").conversation_id == active.conversation_id
