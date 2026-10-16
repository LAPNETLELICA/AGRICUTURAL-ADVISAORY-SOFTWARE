# Backend Agricultural Technical File Design

**Status:** Design approved in chat on 2026-10-16; awaiting written-spec review.

## Goal and scope

Produce a readable, offline-capable, professional PDF technical file from an actual
saved recommendation. This repository contains the FastAPI backend but no Flutter or
web frontend, so this change supplies a stable integration contract and no UI code.
The existing advisory engine and T1–T7 rules remain the only source of agronomic
decisions. Existing API paths stay unchanged.

## Current state and constraints

- `POST /api/v1/advisory/mobile` and questionnaire completion produce a saved
  `Recommendation` and `TraceRecord`; the trace contains the input context, weather,
  evaluated rules, and source references.
- `POST /api/v1/technical-fiches` creates a stored draft. Existing read, list, and
  download routes deliver it, while Education lists visible files and download URLs.
- The current PDF writer uses Latin-1 replacement and emits a flat text dump. This
  corrupts French characters and cannot reliably present nine structured sections,
  tables, or long content.
- The questionnaire currently publishes its personalized fiche automatically. This
  conflicts with the private-by-default requirement.
- Profiles store language and knowledge level, but the backend has no system for
  translating governed rule text. No translation or agronomic detail may be invented.

## Data flow and document model

The fiche assembler consumes the saved recommendation, its trace, the available
profile, and the referenced governed rules. It uses a strict allowlist for each
field. A personal fiche remains associated with its owner and recommendation ID;
the PDF is rendered from the stored fiche content, not from a second advisory run.
The questionnaire completion path may create the fiche automatically as a private
draft. Direct mobile advice uses the existing create route on demand. Repeated
create requests for the same owner and recommendation should return the existing
personal fiche where possible.

The stored content contains nine ordered sections:

1. Cover: application name, document title, crop, problem/objective, available
   locality, generation date, fiche ID, and actual validation status.
2. Executive summary: reported objective, engine finding, principal action,
   supported urgency if any, cautious expected outcome, and first step.
3. Farm and crop context: only available crop, variety, location, terrain, soil,
   stage, area, practices, season, and qualified weather observations.
4. Diagnosis and analysis: separately labelled user observations, image-analysis
   results if present, rule-based inferences, supporting evidence, uncertainty,
   alternative explanations, and missing information. Never upgrade a suspicion
   into a confirmed diagnosis or fabricate confidence.
5. Personalized recommendation: the actual primary recommendation, reasons,
   numbered supported actions, supported materials and methods from existing
   `action_guidance`, warnings, limitations, and safe alternatives if present.
6. Implementation plan: a flowing table with action, instruction, period/date,
   materials, and status. Dates and quantities appear only when their inputs and
   valid calculation are available. No generic date is assigned to every action.
7. Monitoring: available indicators and warnings, a practical checklist,
   reassessment guidance, useful observations to record, and existing follow-up
   recommendation guidance without invented inspection intervals.
8. Risks and assistance: relevant recommendation and weather risks, supported
   safety guidance, and referral category/link only when the existing contact
   recommendation warrants it; no invented professional or vendor identity.
9. References and traceability: source titles and URIs from evaluated rules,
   actual rule status and version, recommendation/document IDs and dates,
   supported weather provenance/time, missing-source notice, and limitations.

Missing optional fields are omitted or labelled “Not provided.” A missing,
insufficient-evidence, or contradictory recommendation yields an explicitly
preliminary, limited document without unsupported treatment instructions. An
unusable recommendation is rejected with a safe API response.

## Language and PDF rendering

Use a Unicode-capable PDF renderer with a redistributable embedded font so French
accents and other supported Latin characters survive printing and text extraction.
The deployment image must contain the renderer and font; no host-only font path is
allowed. Render A4 pages with cover, headings, margins, wrapped paragraphs,
long-table pagination, page numbers, and clear safety notices. Escape all
untrusted text before passing it to rich-text components. Return `application/pdf`
with attachment disposition on the existing download route. Render in memory;
no persistent temporary file is needed.

Select English or French document labels from the saved language/profile setting;
unsupported language settings fall back to English and state that fallback in
the document. Keep agricultural recommendation text in the original governed
source language because there is no safe translation pipeline. If it differs
from the label language, state that the agronomic wording is retained unchanged.
Knowledge-level presentation may alter explanations or layout, never the
underlying prescription.

## Privacy, failures, and compatibility

New personalized fiches remain private drafts. Remove automatic publication on
questionnaire completion. A `PUBLISHED` status alone must not expose a personal
fiche: legacy generated records default to private, and publication requires an
explicitly generalized, reviewed educational document. Preserve existing routes
and response shapes where possible; add only safe optional metadata.

No raw exception, stack trace, provider URL, API key, internal path, or provider
diagnostic enters stored fiche content or PDF. Weather is rendered from selected
human-readable values with units, provenance/time only when available; numeric
`month` is not presented as a weather warning. Failures in lookup or rendering
return a sanitized HTTP error and do not produce a corrupt PDF. Authorization is
checked before reading or downloading, including on the Education listing.

## Verification and handoff

Automated tests cover all nine sections, real recommendation/trace values,
missing information, unsupported language fallback, French Unicode extraction,
long multi-page tables, private-by-default access, old published personal files,
rendering failure, safe provider diagnostics, and unchanged recommendation flow.
Inspect a generated sample with `pdfinfo` and `pdftotext` and run the full Python
suite and quality checks. Update the mobile API handoff with create, list, and
download examples; the future frontend can implement the button using those
existing routes.
