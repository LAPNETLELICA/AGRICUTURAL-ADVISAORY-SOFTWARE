# Groq Transcription and Fish Audio Speech Design

> Historical design record recovered from the contact-recommendation feature branch. Provider integration remains a separate, unimplemented proposal unless verified in source.

## Goal

Enable authenticated voice input and spoken advisory output without changing the
existing agricultural reasoning. Groq transcribes farmer audio; Fish Audio turns
the already-generated advisory response into speech. API keys remain server-side.

## Configuration

Proposed placeholder-only entries for `.env.example`:

```dotenv
GROQ_API_KEY=
FISH_AUDIO_API_KEY=
SPEECH_PROVIDER=fish_audio
TRANSCRIPTION_PROVIDER=groq
```

The real `.env` is local and ignored by Git. Settings must never log, serialize,
or return either key. Missing keys disable only their respective provider and retain
the existing text fallback.

## Architecture

`GroqTranscriptionProvider` sends supported uploaded audio to Groq's transcription
API using the configured `GROQ_API_KEY`. A proposed authenticated transcription
endpoint returns text and detected/requested language; it does not create a second
advisory engine.

`FishAudioSpeechProvider` sends formatted recommendation text to Fish Audio using
`FISH_AUDIO_API_KEY`. The proposed `/api/v1/advisory/voice` integration uses it when
`SPEECH_PROVIDER=fish_audio`, returns base64 audio on success, and preserves its
existing text response plus a clear fallback reason on timeout/provider failure.

Provider selection belongs in the composition root. Interfaces remain provider
neutral so tests inject fakes and do not make external or paid calls.

## Safety and reliability

- Send keys only in server-to-provider authorization headers.
- Enforce authenticated ownership and media validation before processing.
- Limit accepted audio formats and sizes through the existing media service.
- Apply finite HTTP timeouts and translate external failures into safe provider
  fallback responses.
- Do not store raw audio, transcripts, or generated audio beyond the existing media
  retention/privacy policy unless an explicit storage workflow requests it.

## Testing

Unit tests should cover Settings parsing, missing-key disabled behaviour, request
headers and payloads, successful binary audio, transcription parsing, and timeout/error
fallback. API tests should prove the voice endpoint keeps text available when Fish
Audio is unavailable and the transcription route requires authentication. Tests use
mocked HTTP transports and placeholder keys only.