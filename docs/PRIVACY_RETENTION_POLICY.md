# AgriSense V1 Privacy and Retention Baseline

This file is an implementation baseline and must be reviewed against the law and pilot agreements before production launch.

## Purpose and data minimization

AgriSense stores only information needed to provide crop-centered advice, preserve traceability, support farmer history, deliver SMS, and process optional image evidence. Image evidence is not used for automated disease classification in V1.

## Access

Farmer-owned operational data is exposed only through authenticated endpoints with ownership checks. Administrative and knowledge-management functions require privileged roles. Image objects are stored outside public static paths and can only be retrieved through the authenticated media API.

## Default retention

- Recommendation and trace: 180 days
- Crop/history events: 730 days
- SMS delivery records: 90 days
- Image evidence: 180 days
- Security/audit events: 365 days

All periods are environment-configurable. `scripts/cleanup_retention.py` and `POST /api/v1/admin/retention/run` enforce the configured periods.

## Farmer rights implemented in V1

- `GET /api/v1/privacy/me`: current retention summary
- `GET /api/v1/privacy/export`: export operational data tied to the authenticated farmer
- `DELETE /api/v1/privacy/me?confirm=DELETE`: erase farmer-owned operational data where there is no overriding legal retention requirement

Production operators remain responsible for applying any jurisdiction-specific legal hold, consent, incident-response, or statutory retention requirements.

## External providers

Weather, translation, TTS, and SMS providers must receive only the minimum data needed for their function. Provider credentials are secrets and must not be logged or committed to source control.
