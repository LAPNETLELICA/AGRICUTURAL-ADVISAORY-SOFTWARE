# Adaptive Farmer Questionnaire Design

**Status:** Approved conversational design — implementation plan pending

## Goal

Provide a backend-guided, step-by-step questionnaire that asks only useful
questions before calling the existing recommendation engine. It must stay
simple for beginners, accept free text, voice, and pictures, and preserve the
existing recommendation API and rules.

## Conversation rules

- The flow is adaptive, never a fixed list. Each answer selects the next
  question or ends data collection when enough context is available.
- Region and locality are gathered first. The service searches validated
  region/locality knowledge for every related answer already available,
  including topography, common soil information, climate, agro-ecological
  zone, calendar, and known risks. It asks the farmer only for a fact missing
  or insufficient in that knowledge; terrain is therefore asked only when
  locality/region terrain information is unavailable or too general.
- Every step offers proposed answers and a free-text “my issue is different”
  entry. Free text changes the next question according to its intent.
- Voice is transcribed through the existing transcription endpoint and then
  treated exactly as free text. Picture evidence uses the existing protected
  media upload/image-analysis flow and is requested only when relevant.
- If a crop passport exists, use its prior crop and practice context and ask
  only for missing or changed information. Without a passport, ask prior crop,
  cultivation type, soil texture/type, and usual manure/fertiliser.
- Beginner profiles receive plain language, short choices, and “I do not
  know”. More experienced profiles receive fewer, more detailed prompts.

## Initial intents and questions

1. **Start farming:** region/locality, crop interest or crop discovery,
   cultivation type, soil texture/type, previous crop if no passport, and
   usual manure/fertiliser.
2. **Existing crop problem:** region/locality, crop, stage, symptoms or free
   text, then optional relevant picture evidence.
3. **Soil improvement:** region/locality, soil texture/type, previous crop
   if no passport, current manure/fertiliser practice, and free-text concern.
4. **Planting time:** region/locality, crop, season question, then use the
   validated calendar/knowledge response without unrelated questions.

## Backend boundary

Add a questionnaire service/API that returns the next question, options,
current collected context, and a completion state. On completion it produces
the existing `MobileAdvisoryRequest`; it does not alter engine rule evaluation
or recommendation selection. The service must only use validated existing
knowledge and known passport/locality data; it must not invent terrain or
agronomic facts.

## Safety and verification

- A free-text entry must be accepted on every step.
- No question may be repeated when a passport or accepted answer already
  provides that context.
- Missing locality data may cause a terrain question; known locality must not.
- Voice transcription or image-analysis failure returns a clear recovery
  option and does not discard text/previous answers.
- Questionnaire completion must produce a request accepted by the existing
  mobile advisory endpoint.
