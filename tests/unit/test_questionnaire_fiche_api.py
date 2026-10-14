from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import Mock

from api.questionnaire import AnswerPayload, answer
from engine.models.conversations import AdvisoryConversation
from engine.models.enums import Channel, RecommendationType
from engine.models.requests import MobileAdvisoryRequest
from engine.models.responses import CanonicalRecommendationItem, Recommendation
from services.auth import Principal
from services.questionnaire import QuestionnaireResult


@dataclass
class Fiche:
    fiche_id: str
    status: str


def test_completed_questionnaire_generates_and_publishes_a_technical_fiche() -> None:
    recommendation = Recommendation(request_id="request-1", crop_id="tomato", channel=Channel.MOBILE, primary=CanonicalRecommendationItem(candidate_id="candidate-1", type=RecommendationType.ADVISORY, name="Tomato guidance", summary="Protect the tomato crop.", score=1.0, rank=1), trace_id="trace-1")
    conversation = AdvisoryConversation.create("farmer-1", intent="crop_problem", symptoms="yellow spots", language="fr")
    questionnaire = Mock()
    questionnaire.receive_message.return_value = QuestionnaireResult(conversation=conversation, ready_request=MobileAdvisoryRequest(farmer_id="farmer-1", crop_id="tomato", question="Help"))
    technical_fiches = Mock()
    technical_fiches.from_recommendation.return_value = Fiche("fiche-1", "DRAFT")
    technical_fiches.set_status.return_value = Fiche("fiche-1", "PUBLISHED")
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(questionnaire_service=questionnaire, container=SimpleNamespace(conversations=SimpleNamespace(latest_open=Mock()), engine=SimpleNamespace(advise=Mock(return_value=recommendation)), traces=SimpleNamespace(get=Mock(return_value=SimpleNamespace(future_conditions_used={"weather": {}}))),), technical_fiche_service=technical_fiches)))

    result = answer(AnswerPayload(farmer_id="farmer-1", conversation_id=conversation.conversation_id, answer="Less than one week", language="fr"), request, request.app.state.container, Principal("farmer-1", "farmer"))

    assert result["complete"] is True
    assert result["technical_fiche"]["fiche_id"] == "fiche-1"
    technical_fiches.set_status.assert_called_once_with("fiche-1", "PUBLISHED")
