# Persistent Advisory Conversations Design

## Goal

Allow one farmer to maintain multiple agricultural-advisory conversations.
Each conversation preserves its complete message history and collected context.
The backend must interpret a submitted text message in the context of that
conversation: as a new issue, an answer to the outstanding prompt, or an
unclear response requiring clarification. It must ask only for information
needed to give a reliable recommendation and return that recommendation once
the required facts are available.

## Compatibility

The URLs and existing required fields for `POST /questionnaire/start`,
`POST /questionnaire/answer`, and `POST /questionnaire/complete` remain
unchanged. Each endpoint gains an optional `conversation_id` request field and
returns it. Existing clients that omit it use the farmer's most recently
updated open conversation; a new client must retain and send the identifier.

The additional endpoint `GET /questionnaire/conversations/{conversation_id}`
returns the owned conversation's status, accumulated context, complete ordered
message history, and its final recommendation when available. It allows a
mobile client to reopen any saved conversation without recreating it.

`/questionnaire/answer` keeps accepting `answer`, but treats it as a neutral
farmer message. This preserves the current frontend contract while correcting
the semantic error that all typed questions are answers.

## Data model

Persist conversations in `advisory_conversations` and messages in
`advisory_conversation_messages`.

- A conversation has an opaque UUID, farmer ID, status (`open` or `completed`),
  current intent, expected field, accumulated advisory context, and timestamps.
- A message belongs to one conversation, has an ordered sequence, sender
  (`farmer` or `assistant`), text, optional structured facts extracted from the
  text, and timestamp.
- The database enforces the farmer/conversation relationship and deletes a
  conversation's messages when the conversation is deleted. It indexes farmer
  plus update time and conversation plus sequence.
- The in-memory implementation used by local/test configurations follows the
  same repository interface, but persistent deployments use PostgreSQL.

## Conversation behavior

`start` always creates a new conversation, adds the introductory assistant
message to its history, and returns the existing intent options plus the new
conversation ID.

`answer` loads and authorizes the requested conversation. It records the exact
farmer message before interpreting it. The interpreter first recognizes stable
intent option values and their display labels. For free text it detects a crop
problem, soil-improvement, planting-time, or start-farming intent from a
small, deterministic keyword set. If the conversation is already waiting for
a specific fact, it accepts the text as that fact unless it clearly starts a
different intent; the latter starts a new subject within the same conversation
and resets only intent-specific incomplete facts.

After each message, the service merges facts from the saved context, known
locality knowledge, and the farmer's message. It selects the first missing
field for the active intent:

- Crop problem: crop, symptoms, and current stage or onset.
- Soil improvement: crop, soil/practice concern, and location when unavailable.
- Planting time: crop and region/locality when unavailable.
- Start farming: crop interest/discovery, cultivation details, and missing
  terrain/practice information.

Known locality facts and existing crop-passport data are never requested
again. A typed question therefore begins a conversation rather than being
blindly classified as a response to a nonexistent prompt.

When all required facts for the selected intent are present, `answer` returns
`complete: true` and the recommendation. The recommendation follows the same
mobile-advisory processing path, including media validation, image analysis,
action guidance, contact guidance, and profile-based presentation. Its
assistant result is recorded and the conversation becomes `completed`.

`complete` stays available for clients that explicitly submit a full context.
When given a conversation ID, saved values are merged with the supplied
context; it refuses incomplete contexts with the next required question rather
than fabricating a recommendation.

## Errors and safety

- A missing or unknown conversation ID returns `404`; another farmer's
  conversation returns `403`.
- A farmer with no open conversation who omits `conversation_id` receives a
  clear `400` recovery error instructing the client to call `start`.
- All stored messages are bounded in length, and only validated structured
  context becomes advisory evidence.
- Conversation history records text and assistant prompts, not image contents
  or secrets. Image IDs continue through the existing protected-media checks.

## Tests

Tests cover independent concurrent conversations for one farmer, history
ordering, free-text questions becoming an intent, free-text answers filling a
pending field, visible option labels routing correctly, automatic completion,
legacy fallback behavior, authorization, persistence mapping, and the
unchanged direct completion contract.
