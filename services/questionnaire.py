"""Adaptive, knowledge-first farmer questionnaire."""

from dataclasses import dataclass, field
from typing import Any

from engine.models.conversations import AdvisoryConversation, ConversationMessage, ConversationStatus
from engine.models.requests import EvidenceInput, MobileAdvisoryRequest


@dataclass(frozen=True, slots=True)
class QuestionnaireOption:
    id: str
    label: str


@dataclass(frozen=True, slots=True)
class QuestionnaireStep:
    key: str
    prompt: str
    options: list[QuestionnaireOption] = field(default_factory=list)
    accepts_free_text: bool = True
    known_context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class QuestionnaireResult:
    conversation: AdvisoryConversation
    step: QuestionnaireStep | None = None
    ready_request: MobileAdvisoryRequest | None = None


class QuestionnaireService:
    def __init__(self, knowledge: Any, conversations: Any | None = None) -> None:
        self._knowledge = knowledge
        self._conversations = conversations

    def start_conversation(
        self, *, farmer_id: str, profile_level: str = "beginner", region: str | None = None,
        locality: str | None = None, language: str = "en",
    ) -> QuestionnaireResult:
        if self._conversations is None:
            raise RuntimeError("conversation repository is not configured")
        conversation = AdvisoryConversation.create(
            farmer_id, region=region, locality=locality, profile_level=profile_level, language=language
        )
        self._conversations.create(conversation)
        step = self.start(profile_level=profile_level, region=region, locality=locality)
        conversation = conversation.model_copy(update={"expected_field": step.key})
        self._conversations.save(conversation)
        self._append(conversation, "assistant", step.prompt)
        return QuestionnaireResult(conversation=self._get(conversation.conversation_id), step=step)

    def receive_message(self, conversation_id: str, message: str) -> QuestionnaireResult:
        conversation = self._get(conversation_id)
        if conversation.status is ConversationStatus.COMPLETED:
            raise ValueError("conversation is already completed")
        self._append(conversation, "farmer", message)
        normalized = message.casefold().strip()
        context = dict(conversation.context)
        if conversation.expected_field == "intent":
            intent = self._intent(normalized, conversation.intent)
            context = {
                key: value
                for key, value in context.items()
                if key in {"region", "locality", "profile_level", "language"}
            }
            context["intent"] = intent
        else:
            intent = conversation.intent or "free_text"
        facts = self._extract(normalized)
        if conversation.expected_field == "onset":
            facts["onset"] = message
        elif conversation.expected_field and conversation.expected_field != "crop":
            facts[conversation.expected_field] = self._option_value(conversation.expected_field, normalized, message)
        context.update(facts)
        conversation = conversation.model_copy(update={"intent": intent, "context": context})
        if intent == "crop_problem" and all(context.get(key) for key in ("crop_id", "symptoms", "onset")):
            question = next(
                (item.text for item in self._conversations.list_messages(conversation_id) if item.sender == "farmer"),
                message,
            )
            ready = MobileAdvisoryRequest(
                farmer_id=conversation.farmer_id,
                crop_id=str(context["crop_id"]),
                question=question,
                region=context.get("region"),
                locality=context.get("locality"),
                current_stage=context.get("onset"),
                evidence=EvidenceInput(observations={"symptoms": context["symptoms"]}),
            )
            conversation = conversation.model_copy(
                update={"expected_field": None, "status": ConversationStatus.COMPLETED}
            )
            self._conversations.save(conversation)
            return QuestionnaireResult(conversation=self._get(conversation_id), ready_request=ready)
        if intent == "start_farming" and all(
            context.get(key) for key in ("crop_id", "topography", "previous_crop", "usual_manure")
        ):
            ready = MobileAdvisoryRequest(
                farmer_id=conversation.farmer_id,
                crop_id=str(context["crop_id"]),
                question=f"I want to grow {context['crop_id']}.",
                region=context.get("region"),
                locality=context.get("locality"),
                evidence=EvidenceInput(practices={"usual_manure": context["usual_manure"]}),
            )
            conversation = conversation.model_copy(
                update={"expected_field": None, "status": ConversationStatus.COMPLETED}
            )
            self._conversations.save(conversation)
            return QuestionnaireResult(conversation=self._get(conversation_id), ready_request=ready)
        step = self._next_step(conversation)
        conversation = conversation.model_copy(update={"expected_field": step.key})
        self._conversations.save(conversation)
        self._append(conversation, "assistant", step.prompt)
        return QuestionnaireResult(conversation=self._get(conversation_id), step=step)

    def get_conversation(self, conversation_id: str) -> tuple[AdvisoryConversation, list[ConversationMessage]]:
        return self._get(conversation_id), self._conversations.list_messages(conversation_id)

    def _get(self, conversation_id: str) -> AdvisoryConversation:
        if self._conversations is None:
            raise RuntimeError("conversation repository is not configured")
        conversation = self._conversations.get(conversation_id)
        if conversation is None:
            raise KeyError(conversation_id)
        return conversation

    def _append(self, conversation: AdvisoryConversation, sender: str, text: str) -> None:
        messages = self._conversations.list_messages(conversation.conversation_id)
        sequence = len(messages) + 1
        factory = ConversationMessage.farmer if sender == "farmer" else ConversationMessage.assistant
        self._conversations.append_message(conversation.conversation_id, factory(sequence, text))

    @staticmethod
    def _intent(message: str, current: str | None) -> str:
        if message in {"start farming", "start_farming"}:
            return "start_farming"
        if message in {"existing crop problem", "crop problem", "crop_problem"}:
            return "crop_problem"
        if message in {"improve soil", "soil improvement"} or "soil" in message:
            return "soil"
        if message in {"when to plant", "planting time"} or "plant" in message:
            return "planting"
        if any(word in message for word in ("spot", "leaf", "leaves", "yellow", "pest", "disease")):
            return "crop_problem"
        return current or "free_text"

    @staticmethod
    def _option_value(field: str, normalized: str, message: str) -> str:
        aliases = {
            "flat": "flat",
            "sloping": "sloping",
            "low/wet": "low_wet",
            "i do not know": "unknown",
            "no previous crop": "none",
            "poultry manure": "poultry_manure",
            "cattle manure": "cattle_manure",
            "compost": "compost",
        }
        return aliases.get(normalized, message)

    @staticmethod
    def _extract(message: str) -> dict[str, Any]:
        crops = {"tomato": "tomato", "maize": "maize", "corn": "maize", "potato": "irish-potato", "bean": "bean", "cassava": "cassava"}
        found = next((crop_id for word, crop_id in crops.items() if word in message), None)
        facts: dict[str, Any] = {}
        if found:
            facts["crop_id"] = found
        if any(word in message for word in ("spot", "yellow", "pest", "disease", "leaf")):
            facts["symptoms"] = message
        return facts

    def _next_step(self, conversation: AdvisoryConversation) -> QuestionnaireStep:
        context = conversation.context
        known = self._known_context(context.get("region"), context.get("locality"))
        if conversation.intent == "crop_problem":
            if not context.get("crop_id"):
                return QuestionnaireStep("crop", "Which crop has this problem?", self._crop_options(), known_context=known)
            if not context.get("symptoms"):
                return QuestionnaireStep("symptoms", "What symptoms do you see?", known_context=known)
            return QuestionnaireStep("onset", "When did the problem start?", self._onset_options(), known_context=known)
        if conversation.intent == "start_farming":
            if not context.get("crop_id"):
                return QuestionnaireStep("crop", "Which crop do you want to grow?", self._crop_options(), known_context=known)
            if not context.get("topography"):
                return QuestionnaireStep("topography", "Is your land flat, sloping, or low/wet?", self._topography_options(), known_context=known)
            if not context.get("previous_crop"):
                return QuestionnaireStep("previous_crop", "What crop was cultivated here before?", self._previous_crop_options(), known_context=known)
            return QuestionnaireStep("usual_manure", "What manure or fertiliser do you usually use?", self._manure_options(), known_context=known)
        if conversation.intent == "planting":
            return QuestionnaireStep("crop", "Which crop do you want to plant?", self._crop_options(include_unknown=False), known_context=known)
        if conversation.intent == "soil":
            return QuestionnaireStep("soil_concern", "What soil or fertiliser problem do you have?", known_context=known)
        return QuestionnaireStep("free_text", "Please describe your agricultural question.", known_context=known)

    def start(
        self, *, profile_level: str, region: str | None = None, locality: str | None = None
    ) -> QuestionnaireStep:
        del profile_level
        context = self._known_context(region, locality)
        return QuestionnaireStep(
            key="intent",
            prompt="What do you need help with today? You may also type your own question.",
            options=[
                QuestionnaireOption("start_farming", "Start farming"),
                QuestionnaireOption("crop_problem", "Existing crop problem"),
                QuestionnaireOption("soil", "Improve soil"),
                QuestionnaireOption("planting", "When to plant"),
            ],
            known_context=context,
        )

    def answer(self, context: dict[str, Any], answer: str) -> QuestionnaireStep:
        known = self._known_context(context.get("region"), context.get("locality"))
        normalized_answer = answer.casefold()
        if any(word in normalized_answer for word in ("spot", "leaf", "leaves", "yellow", "pest")):
            return QuestionnaireStep(
                key="crop_problem",
                prompt="Please describe when the problem started. You can also add a picture if available.",
                options=["Less than one week", "More than one week", "I do not know"],
                known_context=known,
            )
        if answer == "start_farming" and not known:
            return QuestionnaireStep(
                key="topography",
                prompt="I do not have terrain information for your locality. Is your land flat, sloping, or low/wet?",
                options=["Flat", "Sloping", "Low/wet", "I do not know"],
            )
        if answer == "start_farming":
            return QuestionnaireStep(
                key="previous_crop",
                prompt="What crop was cultivated here before, and what manure or fertiliser do you usually use?",
                options=["No previous crop", "Poultry manure", "Cattle manure", "Compost", "I do not know"],
                known_context=known,
            )
        return QuestionnaireStep(
            key="free_text",
            prompt="Please describe your issue, or choose an option above.",
            known_context=known,
        )

    @staticmethod
    def _crop_options(*, include_unknown: bool = True) -> list[QuestionnaireOption]:
        options = [
            QuestionnaireOption("tomato", "Tomato"),
            QuestionnaireOption("maize", "Maize"),
            QuestionnaireOption("irish-potato", "Potato"),
        ]
        if include_unknown:
            options.append(QuestionnaireOption("unknown", "I do not know"))
        return options

    @staticmethod
    def _onset_options() -> list[QuestionnaireOption]:
        return [
            QuestionnaireOption("less_than_one_week", "Less than one week"),
            QuestionnaireOption("more_than_one_week", "More than one week"),
            QuestionnaireOption("unknown", "I do not know"),
        ]

    @staticmethod
    def _topography_options() -> list[QuestionnaireOption]:
        return [
            QuestionnaireOption("flat", "Flat"),
            QuestionnaireOption("sloping", "Sloping"),
            QuestionnaireOption("low_wet", "Low/wet"),
            QuestionnaireOption("unknown", "I do not know"),
        ]

    @staticmethod
    def _previous_crop_options() -> list[QuestionnaireOption]:
        return [
            QuestionnaireOption("none", "No previous crop"),
            QuestionnaireOption("unknown", "I do not know"),
        ]

    @staticmethod
    def _manure_options() -> list[QuestionnaireOption]:
        return [
            QuestionnaireOption("poultry_manure", "Poultry manure"),
            QuestionnaireOption("cattle_manure", "Cattle manure"),
            QuestionnaireOption("compost", "Compost"),
            QuestionnaireOption("unknown", "I do not know"),
        ]

    def complete(self, context: dict[str, Any]) -> MobileAdvisoryRequest:
        """Map collected answers to the unchanged mobile advisory contract."""
        practices = {"usual_manure": context["usual_manure"]} if context.get("usual_manure") else {}
        return MobileAdvisoryRequest(
            farmer_id=str(context["farmer_id"]),
            crop_id=context.get("crop_id"),
            crop_description=context.get("crop_description"),
            crop_discovery=bool(context.get("crop_discovery", False)),
            question=str(context["question"]),
            region=context.get("region"),
            locality=context.get("locality"),
            evidence=EvidenceInput(practices=practices),
        )

    def _known_context(self, region: str | None, locality: str | None) -> dict[str, Any]:
        raw = self._knowledge.locality_context(region, locality)
        if not raw:
            return {}
        return {
            "topography": {"altitude_m": raw.get("altitude_m")},
            "soil_types": raw.get("sols", []),
            "local_risks": raw.get("risques_locaux", []),
            "agricultural_profile": raw.get("profil_agricole"),
        }
