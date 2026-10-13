from pathlib import Path

from integrations.cameroon_knowledge import CameroonKnowledgeProvider
from services.questionnaire import QuestionnaireService


def test_known_locality_uses_knowledge_before_asking_terrain() -> None:
    knowledge = CameroonKnowledgeProvider(Path("BASE_CONNAISSANCES_AGRICOLES"))
    step = QuestionnaireService(knowledge).start(profile_level="beginner", region="West", locality="Bafoussam")
    assert step.key == "intent"
    assert "topography" in step.known_context
    assert step.accepts_free_text is True


def test_unknown_locality_asks_for_terrain_when_needed() -> None:
    knowledge = CameroonKnowledgeProvider(Path("BASE_CONNAISSANCES_AGRICOLES"))
    step = QuestionnaireService(knowledge).answer({"region": "West", "locality": "Unknown"}, "start_farming")
    assert step.key == "topography"


def test_free_text_question_changes_the_next_step() -> None:
    knowledge = CameroonKnowledgeProvider(Path("BASE_CONNAISSANCES_AGRICOLES"))
    step = QuestionnaireService(knowledge).answer(
        {"region": "West", "locality": "Bafoussam"},
        "My tomato leaves have spots",
    )

    assert step.key == "crop_problem"
    assert "picture" in step.prompt.lower()
