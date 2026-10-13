# Regional SMS Delivery Design

**Date:** 2026-10-09  
**Status:** Approved design — implementation plan pending

## Purpose

Add a reliable SMS delivery capability for registered Cameroon phone numbers.
SMS is an optional notification channel. It must not change, delay, or be
required by the normal advisory/recommendation API.

An administrator manages phone registrations and sends manual broadcasts from
the existing admin dashboard. A separate proactive process may also deliver
important alerts produced by the existing rule-based decision forest.

## Confirmed requirements

- There is **no OTP**, phone verification, or reply workflow.
- A registration stores only an active phone number and its region/location.
  It must not collect crop, farm-profile, or other farmer details for SMS.
- A registered, active number can receive either a manual broadcast or an
  automatic engine alert.
- All delivery is location-specific. An alert for South Region must never be
  sent to a Centre Region registration. A Cameroon-wide alert may target all
  active registrations.
- Manual broadcasts are selected by individual registered number, region, or
  all active registrations.
- Automatic messages originate from the existing engine and validated
  `BASE_CONNAISSANCES_AGRICOLES` knowledge only. The SMS layer makes no
  agricultural decision and must not invent guidance.
- Weather-triggered messages remain inactive until an actual WeatherAPI key
  and validated weather-aware rules are available.
- Tranzak is the active delivery gateway when configured. The existing SMS
  simulator remains available for local development and tests.
- Secret provider credentials stay in `.env`; they are never entered into or
  returned by the dashboard.

## Boundaries

### Recommendation engine

The recommendation API remains request-driven and independent. It can produce
normal recommendations whether SMS is enabled, disabled, failing, or not
configured. The proactive process consumes a clearly defined engine alert
output; it cannot modify recommendation ranking, rules, or application
responses.

### SMS delivery

The SMS subsystem has three responsibilities only:

1. maintain registered phone number and region records;
2. route manual or engine-generated messages to matching registrations; and
3. record delivery attempts and provider outcomes.

It uses an explicit region target supplied by an administrator (manual) or by
the engine (automatic). There is no crop-based filtering in SMS registration.

## Data model

### SMS registration

Persist one record per registered phone number with:

- immutable identifier;
- normalized E.164 Cameroon phone number (`+237...`);
- display/entered number for administration, if useful;
- canonical Cameroon region;
- `active` status;
- created and updated timestamps.

The admin can create, edit region, enable/disable, and delete a registration.
Deleting a registration must not erase retained delivery audit records; those
records retain a non-secret recipient snapshot.

### Delivery and alert records

Persist a delivery record for every attempted manual or automatic message:

- source (`manual` or `automatic`);
- recipient registration and normalized number snapshot;
- target scope (individual, region, or Cameroon-wide);
- message text and bounded length;
- delivery state (`pending`, `sent`, `failed`, or provider-accepted state);
- provider name, provider message/reference identifier, and safe failure
  reason;
- timestamps;
- automatic alert fingerprint where applicable.

Automatic-alert fingerprints prevent a number receiving the same engine alert
more than once within its defined alert window. A new engine alert, a changed
alert, or an expiry of that window can permit a later delivery.

## Provider integration

Create a Tranzak adapter behind the existing `SMSProvider` boundary. It will:

- obtain and refresh a Tranzak bearer token using app credentials;
- send messages using Tranzak's SMS endpoint;
- preserve the provider reference and failure details in delivery history;
- use connection and response timeouts; and
- fail safely without breaking the advisory API.

Add documented `.env` settings for provider selection, Tranzak sandbox or
production base URL, application ID, application key, sender ID, timeout, and
the Cameroon default country prefix. `.env.example` contains placeholders
only. Actual credentials do not appear in committed files or dashboard
responses.

The simulator remains selectable through `SMS_PROVIDER=simulator`. The
database/persistence layer records delivery history independently of which
gateway is selected.

## API and dashboard

Add admin-protected endpoints and dashboard views for:

- list/create/update/deactivate/delete registrations;
- list active registrations by region;
- create and preview manual broadcasts before submission;
- submit a manual broadcast to individual numbers, one region, or all active
  numbers;
- list delivery history and provider status; and
- view or change automatic-alert enablement and check interval.

The dashboard displays provider readiness (configured, simulator, or missing
configuration) but never displays raw credentials. It must make the selected
recipient count and regional scope visible before a manual broadcast is sent.

Existing `/api/v1/advisory/sms`, simulator, virtual inbox, and notification
sandbox endpoints retain their current behavior until deliberately migrated or
adapted behind compatible boundaries.

## Automatic alert flow

Add a dedicated proactive-alert worker, following the existing Docker worker
pattern. On each configured interval it:

1. retrieves active registrations grouped by region;
2. requests a region-scoped alert assessment from the existing engine;
3. accepts only actionable outputs with a clear target scope;
4. filters registrations strictly by that scope;
5. checks the fingerprint/deduplication record for each candidate; and
6. queues and sends eligible messages through the selected SMS provider.

If weather configuration, validated knowledge, or usable engine evidence is
missing, the worker skips that alert category and records a safe diagnostic;
it does not guess or broadcast generic agricultural advice.

The worker is isolated from the advisory API. A provider outage records failed
delivery and may be retried according to bounded retry policy; it does not
affect normal recommendation requests.

## Region matching

Use a canonical controlled list of Cameroon regions. Admin input is normalized
to that list. The matching rules are explicit:

- `region:<name>` targets active registrations in exactly that region;
- `cameroon` targets all active registrations; and
- `registration:<id>` targets the named active registration only.

No automatic message is sent without one of these explicit scopes. Locality
may later refine a regional target but is not required for this release.

## Configuration and deployment

Add the proactive worker as a Docker Compose service with the same database,
knowledge, provider, and non-secret runtime configuration needed to run.
The default check interval is one hour and is configurable by environment and
admin settings. The worker runs only when automatic alerts are enabled.

The currently configured WeatherAPI adapter is used only after the user places
a real key in `.env`; no key is stored in code. The user-facing recommendation
application remains usable without it.

## Error handling and security

- Validate and normalize all phone numbers before persisting or sending.
- Require administrator authorization for registration management, broadcasts,
  delivery history, and automatic-alert settings.
- Limit message length according to configured SMS limits before provider
  submission.
- Use safe, non-secret audit logs and error messages.
- Do not expose phone lists to non-admin users.
- Do not transmit a message outside its explicit scope.

## Verification

Tests must cover:

- Cameroon number acceptance and `+237` normalization;
- registration CRUD and admin authorization;
- manual recipient selection and preview;
- exact regional routing and Cameroon-wide routing;
- rejection/skipping of messages without an explicit scope;
- automatic engine alert routing and deduplication;
- no impact on ordinary recommendation requests when SMS fails or is disabled;
- Tranzak request/token/error handling with mocked HTTP; and
- simulator fallback, delivery history, and dashboard API behavior.

## Out of scope

- OTP and phone-number verification;
- crops or farm details in SMS registration;
- automatic image-based disease diagnosis;
- inventing agricultural thresholds or advice outside validated knowledge;
- changing the normal recommendation algorithm.
