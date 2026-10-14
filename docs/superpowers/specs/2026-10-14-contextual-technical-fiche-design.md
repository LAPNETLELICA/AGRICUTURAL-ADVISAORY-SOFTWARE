# Contextual Technical Fiche Design

**Status:** Approved design — implementation plan pending

## Goal

Repair the adaptive questionnaire progression and produce a professional,
contextual technical fiche from its final advisory recommendation. The fiche
must be readable in the Education experience and downloadable as a correctly
paginated PDF.

## Scope and explicit deferrals

- The questionnaire must progress after every accepted response and must never
  repeat an already answered step.
- The API must use stable option identifiers independently of their displayed
  labels, while continuing to accept legacy display values sent by existing
  Flutter clients.
- `language` continues to be accepted and persisted in the API contract, but
  full localisation of questionnaire copy, recommendations, education and
  fiches is deferred. Current copy remains in its existing language.
- A configured weather provider is a supported data source. When weather is
  relevant and available, its useful forecast or warning is rendered as advice.
  Provider failures are never rendered as farmer-facing advisory text.

## Questionnaire contract and state machine

`/api/v1/questionnaire/start` creates a conversation and returns the first
step. `/answer` receives the conversation identifier, answer and contextual
fields. Each response is canonicalised against the previous step's option IDs
and aliases, then stored under that step key before selecting the next state.

The returned option shape becomes `{ "id": "start_farming", "label":
"Start farming" }`. The answer endpoint accepts either `id` or the legacy
string label, ensuring existing Flutter versions do not loop. A response
returns either a different `step.key`, or `complete: true` with a recommendation
and the generated fiche reference.

Each supported intent has an explicit completion path. It gathers only data
needed for the intent, reuses known locality/passport facts, maps the context to
the existing `MobileAdvisoryRequest`, and invokes the unchanged advisory engine.

## Fiche assembly

The fiche builder consumes the final conversation context, recommendation and
known locality data. It selects only relevant sections instead of producing a
generic dump:

1. **Informations générales** — farmer/exploitation when authorised and
   available, locality/parcelle/superficie, crop/variety, stage, advice date
   and adviser contact.
2. **Diagnostic et observations** — stated need, observed symptoms, relevant
   soil/plant/pest observations, and target outcome.
3. **Recommandations et plan d'action** — dynamically selected cultural/soil,
   fertilisation, crop-protection or biocontrol, and irrigation sections. It
   preserves validated engine facts and uses practical field units only where
   a governed recommendation provides them.
4. **Calendrier des actions et suivi** — chronological rows with action,
   period/deadline and status.
5. **Mises en garde et sécurité** — warnings, weather-aware constraints,
   applicator safety and pre-harvest interval only when the evidence provides
   it, plus prevention advice.
6. **Prochaine étape et contact** — follow-up date/action and support contact
   when available.

Missing optional farmer facts are shown only as an explicit neutral “À
confirmer” field where it is useful for follow-up; no internal exception or
provider error is exposed.

## PDF and Education delivery

The download endpoint creates an A4 document with section hierarchy, wrapping,
action-calendar table, exact page totals and page footer. It is generated from
the same structured fiche returned by the API, so preview and download cannot
diverge. The Education API adds a published-fiche feed/detail that delegates to
the fiche service and returns its download URL; publication and ownership rules
remain enforced by the technical-fiche API.

## Error handling and compatibility

Malformed/stale answers receive a clear business error with the expected step
key, rather than silently repeating a question. Legacy option labels remain
valid. Ownership checks, sanitisation of private fields and published-only
public reading remain unchanged.

## Testing

Tests cover: legacy label and stable-ID answers moving from `intent` to a new
step; each completion branch; no repeated keys; generated fiche section
selection; suppression of provider-error text; weather advice when supplied;
valid multi-page PDF response and headers; Education listing/detail/download;
and language field persistence without localisation assertions.
