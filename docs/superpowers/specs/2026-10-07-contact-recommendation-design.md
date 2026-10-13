# Contact Recommendation and Verified Contact Management

## Purpose

Extend the backend so every completed AGIADVISE recommendation is evaluated for
optional follow-up support. The existing deterministic agricultural engine remains
the only source of crop, soil, weather, image, regional, calendar, topography and
T1–T7 reasoning. The extension only decides whether that completed recommendation
indicates a need for a qualified specialist or a relevant vendor, and exposes
verified contacts that the client may present to the farmer.

The backend must never initiate a call, WhatsApp message, email, or transfer user
data to a contact.

## Existing boundaries to preserve

`AdvisoryEngine.advise()` assembles agricultural context, selects and evaluates the
knowledge forest, applies constraints, scores/ranks candidates, and creates the
canonical `Recommendation`. `RecommendationBuilder` remains unchanged as the
agricultural recommendation author. `api/mobile.py` currently adapts that result
for a user profile immediately before returning it.

This feature must not copy T1–T7 rules, inspect the knowledge forest, replace the
engine with an LLM, or alter the agricultural conclusion, actions, warnings,
candidate ranking, trace, or recommendation persistence.

## Architecture and data flow

1. The existing engine produces and persists a canonical `Recommendation` exactly
   as it does today.
2. The mobile API supplies that recommendation plus existing request evidence to
   `ContactRecommendationService`.
3. The service reads only recommendation output and evidence metadata already
   produced by the system: primary/alternative identifiers and types, action text,
   warning text, uncertainty, score data, and image-analysis relevance/summary.
4. The service returns a structured `ContactRecommendation` value. The API attaches
   it to a response copy; it does not mutate the recommendation used for engine
   traces or persistence.
5. The client uses the flags to decide whether to render a specialist and/or vendor
   navigation action. It requests contacts separately using the returned category,
   crop, and user-selected location filters.

The post-processing location is intentionally outside `AdvisoryEngine`: contact
routing is application behaviour, not agricultural decision making. The evaluator
will live in `services/contact_recommendation.py` and be constructed in the FastAPI
application factory.

## Contact recommendation contract

Add the following optional field to `Recommendation`; existing fields and response
shape otherwise stay compatible.

```json
{
  "contact_recommendation": {
    "specialist_required": false,
    "vendor_required": true,
    "specialist_reason": null,
    "vendor_reason": "The recommendation requires an agricultural input.",
    "specialist_category": null,
    "vendor_category": "fertilizer"
  }
}
```

All six keys are always serialised when the field exists. Reasons and categories
are `null` when their corresponding flag is false. A no-support result has both
flags false and all other values null.

Categories are a small shared vocabulary, initially:

- Specialist: `crop_disease`, `soil_analysis`, `field_assessment`,
  `agronomy_general`.
- Vendor: `seed`, `fertilizer`, `soil_amendment`, `agricultural_treatment`,
  `irrigation_equipment`, `agricultural_service`.

The evaluator maps existing action/warning/candidate labels to those categories.
It does not create an agricultural diagnosis. It must require a specialist for the
existing insufficient-evidence recommendation, explicit professional/field/lab
assessment wording, serious/uncertain warnings, or unusable/insufficient image
evidence. It must require a vendor only when existing actions or candidate labels
explicitly require an obtainable input, equipment, or service. Both outcomes may
be true independently.

Mapping rules are deliberately centralized and unit-tested. Unknown wording is
conservative: it produces neither a vendor recommendation nor a new diagnosis.

## Contact persistence

Create an `agricultural_contacts` table rather than extending an unrelated model;
the current schema has no provider/contact entity. One record represents one
specialist or vendor and contains:

- `contact_id`, `name`, `contact_type`, `description`
- `specialization`, `category`, `crop_ids`
- `region`, `location`, `address`
- `phone`, `whatsapp`, `email`
- `verified`, `active`, `created_at`, `updated_at`

`contact_type` is constrained in application validation to `SPECIALIST` or
`VENDOR`; category uses the shared vocabulary above. `crop_ids` is a JSON document
to match the existing database portability convention. Indexes support type,
category, region, and the public verified/active query.

A repository/service owns CRUD and filtering. It supports the configured
PostgreSQL database only; public/contact management endpoints return a clear 503
when persistence is not configured, matching existing database-backed services.

## Public contact discovery API

Add a public, authenticated router under `/api/v1/contacts`:

- `GET /specialists`
- `GET /vendors`

Both endpoints accept optional `category`, `crop_id`, `region`, and `location`
filters. They always enforce the endpoint's contact type and `verified=true`,
`active=true`. Results are ranked by exact category, crop support, and region/
location match, then name. They expose only contact-card data and omit any internal
administrative fields. Empty contact fields remain null so a client can omit a
Call, WhatsApp, or Email action that cannot work.

No endpoint receives a farmer profile, recommendation trace, auth token, password,
or conversation content for the purpose of passing it to a contact.

## Administration API

Extend the existing admin router—do not build another dashboard/API—with
admin-authorized endpoints at `/api/v1/admin/contacts`:

- `GET /` with `type`, `category`, `region`, `verified`, `active`, and free-text
  `query` filters.
- `POST /` to create a contact.
- `GET /{contact_id}` and `PATCH /{contact_id}` to inspect/edit it.
- `POST /{contact_id}/verification` to set verified/unverified.
- `POST /{contact_id}/activation` to set active/inactive.

Write operations validate at least one usable communication field when a contact
is activated, validate email/phone field formats, and write an audit event that
names the administrator, action, contact ID, and changed fields without storing
secrets. The existing FastAPI OpenAPI dashboard supplies the administrative UI for
this backend-only repository.

## Error handling and compatibility

- Existing advisory requests retain their normal recommendation even if contact
  routing cannot identify a category; their contact result is safely "neither".
- Invalid query/filter payloads return 422 through FastAPI/Pydantic validation.
- Unknown contacts return 404; unavailable persistence returns 503.
- Public discovery never returns inactive or unverified records, including when an
  administrator requests broad query filters through a public route.
- Admin routes retain the current `AdminDependency` authorization policy.

## Testing and acceptance criteria

Add unit tests for evaluation of neither, specialist, vendor, and both; validate
the insufficient-evidence and explicit-input cases; and prove no original
recommendation fields are modified. Add integration tests for public filtering and
ranking, field visibility, 404/503 cases, admin authorization, CRUD, state changes,
and audit events.

The feature is accepted when every mobile recommendation contains a correctly
derived contact result, no normal recommendation loses information, a vendor is
never suggested solely because one exists, and public discovery returns only
relevant verified active contacts.
