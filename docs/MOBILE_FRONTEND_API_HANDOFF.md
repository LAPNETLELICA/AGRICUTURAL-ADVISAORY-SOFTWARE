# AgriAdvise Mobile Frontend API Handoff

Base URL: `https://<host>/api/v1`. Send `Authorization: Bearer <token>` when authentication is enabled. Use JSON except media/audio uploads, which use multipart form data.

Interactive API schema: `https://<host>/docs`. The backend is the source of truth: the mobile app collects and presents information, but does not calculate or hard-code agricultural advice.

Download this handoff from the backend: `GET /api/v1/documentation/mobile-frontend-handoff`.

## Main farmer flow

1. Register or sign in: `POST /auth/register`, `POST /auth/login`; keep the returned token securely.
2. Load profile: `GET /profile/me`; save language/knowledge level with `PUT /profile/me`.
3. Start guided help: `POST /questionnaire/start` with farmer ID, region, locality, and profile level. Save its returned `conversation_id`.
4. Render `step.options` and always show a free-text input because `step.accepts_free_text` is true.
5. Send selected option or typed text plus `conversation_id` to `POST /questionnaire/answer`. The backend records the exact message, understands it as a new farming question or as an answer to the current prompt, and returns only the next needed question.
6. When enough context exists, `/questionnaire/answer` returns `complete: true` and `recommendation`; render it immediately. `POST /questionnaire/complete` remains available for an explicitly collected full context.
7. Reopen a saved conversation with `GET /questionnaire/conversations/{conversation_id}`; it returns the ordered history and collected context. A farmer may keep multiple conversations.
8. For direct/advanced use, call `POST /advisory/mobile` with the same collected context.

Location rule: region/locality knowledge is used first for local soils, climate, risks and terrain context. Ask the farmer only for missing information. A crop passport or prior context prevents repeated questions.

## Voice and pictures

- Voice: upload audio to `POST /advisory/transcribe` (`file`, optional `language`); insert returned `text` into the questionnaire free-text field.
- Picture: upload to `POST /media/images` (`file`, `farmer_id`, optional `crop_id`, `request_id`); put returned `image_id` in `evidence.image_references` when completing/directly requesting advice.
- Optional picture assessment: `POST /image-analysis` with `image_id`, optional `crop_id`, and `analysis_type`; use its result as supporting evidence only. `GET /image-analysis/references` lists supported visual-reference categories.
- Existing crop-problem flow may request a picture; image analysis is evidence, never a replacement for the farmer’s description.

## Farmer endpoints

| Endpoint | Use |
|---|---|
| POST `/auth/register`, `/auth/login` | account and session |
| GET `/auth/me` | current authenticated account |
| GET/PUT `/profile/me` | profile, language and knowledge level |
| POST `/questionnaire/start`, `/answer`, `/complete` | adaptive questionnaire and final recommendation; retain and send optional `conversation_id` |
| GET `/questionnaire/conversations/{conversation_id}` | owned conversation, accumulated context and ordered history |
| POST `/advisory/mobile` | direct recommendation |
| POST `/advisory/voice`, `/advisory/transcribe` | spoken advice and voice-to-text |
| POST `/media/images`; GET/DELETE `/media/images/{image_id}` | protected farmer pictures |
| GET `/media/images/{image_id}/metadata` | picture metadata owned by the farmer |
| POST `/image-analysis`; GET `/image-analysis/references` | optional picture evidence assessment |
| GET `/recommendations/{recommendation_id}` | saved recommendation and trace |
| GET `/crops`, `/crops/{crop_id}` | crop catalogue |
| GET `/education/crops`, `/education/crops/{crop_id}`; POST `/education/learn/curriculum` | learning content |
| GET `/contacts/{contact_type}` | verified specialists/vendors |
| POST `/technical-fiches`; GET `/technical-fiches`, `/{fiche_id}`, `/{fiche_id}/download` | technical fiches |
| GET `/privacy/me`, `/privacy/export`; DELETE `/privacy/me` | privacy controls |

## System and SMS endpoints

| Endpoint | Use |
|---|---|
| GET `/health`, `/ready`, `/knowledge/version` | startup/connection checks |
| POST `/advisory/sms` | legacy recommendation-to-SMS flow |
| POST `/sms/simulate`; GET `/sms/inbox/{recipient_id}` | safe simulator testing |
| POST/GET `/notifications/subscriptions`; POST `/notifications/trigger/{recipient_id}` | legacy notification sandbox |

## Admin dashboard endpoints

Admin token required: GET/POST `/admin/contacts`, contact verification/activation; GET `/admin/overview`, `/admin/knowledge`, `/admin/providers`; POST `/admin/knowledge/import`, `/admin/retention/run`.

### Regional SMS administration

These endpoints are for the administrator dashboard only. A registration contains only a Cameroon telephone number, region, and active status. It never stores a farmer crop, passport, or recommendation context.

1. Register/list recipient numbers: `POST` and `GET` `/admin/sms/registrations`.
2. Before sending a message, call `POST /admin/sms/broadcasts/preview` with a message and scope. Display `recipient_count` for confirmation.
3. Only after confirmation, call `POST /admin/sms/broadcasts/send` with the same payload. It resolves active recipients again at send time and returns `sent`, `failed`, and `recipient_count`.
4. Show delivery audit/history using `GET /admin/sms/deliveries?limit=100`.

For a regional scope, send `{ "kind": "region", "region": "South" }`; for all Cameroon, send `{ "kind": "cameroon" }`. Do not use the mobile farmer application to register numbers or directly trigger broadcasts.

Automatic SMS is separate from the normal recommendation flow. The proactive worker only sends explicitly validated, region-scoped knowledge/engine alerts; it stays idle if alerts are absent, invalid, unscoped, duplicated, or `PROACTIVE_SMS_ENABLED` is false.

The built-in operations pages are `GET /dashboard` and `GET /dashboard/sms-receiver`; they are browser pages, not mobile API endpoints.

## Mobile display rules

- Beginner profile: plain words, one question per screen, options plus free-text, always include “I do not know”.
- Experienced profile: fewer prompts and more detail.
- Never hard-code agriculture advice in the app; show the backend recommendation, actions, warnings and contact guidance.
- Do not put API keys, Tranzak keys, or farmer phone numbers in the mobile app.
- Treat `401` as sign-in required, `403` as an ownership/role restriction, `404` as unavailable content, and a validation `400`/`422` as a form error that should be shown beside the related input.
