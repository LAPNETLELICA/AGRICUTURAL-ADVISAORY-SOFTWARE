# Groq and Fish Audio Implementation Plan

> Historical planning record recovered from the contact-recommendation feature branch. This is not evidence that these integrations have been implemented.

**Goal:** Add optional Groq transcription and Fish Audio recommendation speech with local environment keys and text fallbacks.

**Architecture:** Provider adapters are selected in the composition root from `Settings`; they do not alter the agricultural engine. Fish Audio creates spoken recommendation audio and Groq transcribes authenticated farmer audio.

**Tech Stack:** Python, FastAPI, HTTPX, Pydantic, pytest.

**Spec:** `docs/superpowers/specs/2026-10-08-groq-fish-audio-design.md`

## Global Constraints

- Never commit, return, or log API keys.
- Use placeholder-only `GROQ_API_KEY` and `FISH_AUDIO_API_KEY` configuration.
- Preserve text fallback and existing advisory flow.
- Mock all provider HTTP calls in tests.

---

### Task 1: Configuration and provider selection

**Files:** `engine/config.py`, `engine/bootstrap.py`, `.env.example`, `tests/test_audio_config.py`

- [ ] Write failing tests for blank keys and provider selection.
- [ ] Add non-secret settings for providers, models, voice, and timeout; add blank placeholders to `.env.example`.
- [ ] Select Fish Audio/Groq adapters only when their keys and provider flags are configured; otherwise keep disabled fallbacks.
- [ ] Run `pytest tests/test_audio_config.py -v`.

### Task 2: Provider adapters

**Files:** `integrations/speech/fish_audio.py`, `integrations/speech/groq.py`, `engine/interfaces/providers.py`, `tests/integrations/test_audio_providers.py`

- [ ] Write mocked-HTTP tests for speech, transcription, missing keys, timeout, and provider errors.
- [ ] Implement finite-timeout adapters with provider-neutral errors and no secret leakage.
- [ ] Run `pytest tests/integrations/test_audio_providers.py -v`.

### Task 3: Audio endpoints and documentation

**Files:** `api/voice.py`, `api/app.py`, `README.md`, `tests/integrations/test_api.py`

- [ ] Write tests for authenticated transcription, audio output, and text fallback.
- [ ] Add `/api/v1/advisory/transcribe` using existing media validation; preserve `/voice` text and fallback behaviour.
- [ ] Document local environment configuration and fallback behaviour.
- [ ] Run targeted tests, Ruff, and the full suite.