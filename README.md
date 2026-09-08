# Crop-Centered Agricultural Advisory Engine

Production-oriented V1 backend implementation of the **Crop-Centered Agricultural
Advisory System v3.0** conception book. It implements Developer 1's complete
"HOW TO ADVISE" responsibility and the shared backend work: domain contracts,
provider interfaces, context assembly, API, adapters, Crop Passport, traces,
SMS simulation, integration, and tests.

> **Agronomy safety:** the JSON files currently under `knowledge/` are draft
> demonstration fixtures based
> only on examples in the conception book. They are deliberately labelled `draft`,
> produce a visible warning, and are excluded when `APP_ENV=production`. Developer 2
> must supply sourced and agronomically validated production knowledge.

## What is implemented

| Area | Owner in conception book | Status |
| --- | --- | --- |
| CropTreeSelector (T1 root, dynamic T2-T7 expansion) | Developer 1 | Complete |
| Rule evaluation and evidence capture | Developer 1 | Complete |
| Hard/soft constraints | Developer 1 | Complete |
| MobileScore and SMSPriority strategies | Developer 1 | Complete |
| Deterministic ranking | Developer 1 | Complete |agricultural-advisory-engine/
engine/
advisory/
engine.py
evaluator.py
scoring.py
recommendation.py
# Developer 1 — HOW TO ADVISE
Architecture & Conception Document — 16Crop-Centered Agricultural Advisory System — v3.0
selector.py
# CropTreeSelector
constraints.py
ranking.py
conflict.py
models/
interfaces/
knowledge/
# Developer 2 — WHAT TO ADVISE
crops/
# T1 — crop profiles (root)
soils/
# T2 — soil suitability + improvement rules
regional/
# T3
topography/
# T4
climate/
# T5
timing/
# T6
practices/ risks/
# T7
rules/
integrations/
weather/ translation/ speech/
sms/simulator/
languages/
api/
mobile.py
sms.py
tests/
engine/ rules/ integrations/ scenarios/
| Explicit conflict resolution | Developer 1 | Complete |
| Canonical recommendation generation | Developer 1 | Complete |
| Full decision trace | Developer 1 | Complete |
| Models and interfaces | Shared | Complete |
| Crop Context Builder (Past + Present + Future) | Shared | Complete |
| Crop Passport V1 lifecycle | Shared | Complete, in-memory baseline |
| Weather/translation/TTS/SMS adapter boundaries | Shared | Complete |
| Mobile and proactive SMS API | Shared | Complete |
| SMS virtual inbox/simulator | Shared | Complete |
| Unit, rule, integration, scenario, channel, trace tests | Shared | Complete |
| Validated crop forest and agricultural thresholds | Developer 2 | Merge contract ready; production content pending |
| Flutter application | Separate frontend work | Not part of this Python responsibility |

The V1 engine is an **interconnected rule-based decision forest**, not a machine-
learning random forest. No agricultural threshold is hard-coded in Python. ML-based
disease classification is a V2 extension and must not replace this explainable rule
baseline without validated data and governance.

## Quick start (recommended: `uv`)

```bash
unzip agricultural-advisory-engine.zip
cd agricultural-advisory-engine
uv sync --extra dev
uv run uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

Open:

- API documentation: <http://127.0.0.1:8000/docs>
- Health: <http://127.0.0.1:8000/api/v1/health>
- Crop catalogue: <http://127.0.0.1:8000/api/v1/crops>

In another terminal:

```bash
uv run python scripts/smoke_test.py
uv run pytest
```

## Software to install

### Required

| Software | Supported version | Why |
| --- | --- | --- |
| Python | 3.11 or 3.12 recommended; `<3.14` | Engine and API runtime |
| Git | 2.40+ recommended | Developer 2 merge and source control |
| `uv` | Current stable | Reproducible environment and commands |

### Optional

| Software | Why |
| --- | --- |
| Docker Desktop / Docker Engine + Compose v2 | Containerized run without local Python setup |
| `curl` | Manual endpoint checks and `uv` installer on Linux/macOS |
| VS Code + Python extension | Development convenience only |

### Install commands by operating system

Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y git curl python3 python3-venv python3-pip
curl -LsSf https://astral.sh/uv/install.sh | sh
```

macOS with Homebrew:

```bash
brew install git python@3.12 uv
```

Windows PowerShell with `winget`:

```powershell
winget install --id Git.Git -e
winget install --id Python.Python.3.12 -e
winget install --id astral-sh.uv -e
```

Optional Docker Desktop:

```powershell
winget install --id Docker.DockerDesktop -e
```

Restart the terminal after installing, then verify:

```bash
git --version
python --version
uv --version
```

## Python dependencies

Runtime dependencies are declared in both `pyproject.toml` and `requirements.txt`:

| Package | Version range | Purpose |
| --- | --- | --- |
| FastAPI | `==0.141.1` | REST API and OpenAPI |
| Pydantic | `==2.13.4` | Strict requests, rules, recommendations, and traces |
| Uvicorn | `==0.52.4` | ASGI server |
| Hatchling | `>=1.27,<2` (build-time) | Wheel/editable-install backend |

Development dependencies in `requirements-dev.txt` / the `dev` extra:

| Package | Purpose |
| --- | --- |
| HTTPX | FastAPI integration tests |
| pytest | Unit, rule, integration, and scenario tests |
| pytest-cov | Branch/line coverage |
| Ruff | Formatting and linting |
| mypy | Strict static type analysis |

Install with one of these equivalent methods.

Using `uv`:

```bash
uv sync --extra dev
```

Using `venv` and `pip` on Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Using `venv` and `pip` on Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

If editable extras are blocked by an older `pip`, use:

```bash
python -m pip install -r requirements-dev.txt
python -m pip install --no-deps -e .
```

## Docker run

```bash
docker compose up --build
```

Stop it with `Ctrl+C`, then:

```bash
docker compose down
```

## Repository structure

```text
agricultural-advisory-engine/
├── engine/                       # Developer 1 — HOW TO ADVISE
│   ├── advisory/
│   │   ├── engine.py
│   │   ├── evaluator.py
│   │   ├── scoring.py
│   │   ├── recommendation.py
│   │   ├── selector.py           # CropTreeSelector
│   │   ├── constraints.py
│   │   ├── ranking.py
│   │   └── conflict.py
│   ├── models/                   # Shared contracts
│   └── interfaces/               # Shared provider protocols
├── knowledge/
│   ├── crops/                    # Developer 2 T1 — crop profiles (root)
│   ├── soils/                    # Developer 2 T2
│   ├── regional/                 # Developer 2 T3
│   ├── topography/               # Developer 2 T4
│   ├── climate/                  # Developer 2 T5
│   ├── timing/                   # Developer 2 T6
│   ├── practices/                # Developer 2 T7 practices/rotation
│   ├── risks/                    # Developer 2 T7 crop risks
│   └── rules/                    # Shared JSON rule contract and schemas
├── integrations/                 # Shared replaceable adapters
│   ├── weather/
│   ├── translation/
│   ├── speech/
│   └── sms/simulator/
├── languages/                    # Shared language formatting/handoff
├── api/
│   ├── mobile.py
│   └── sms.py
├── tests/
│   ├── engine/
│   ├── rules/
│   ├── integrations/
│   └── scenarios/
├── scripts/                      # Validation, demo, smoke, offline self-test
├── docs/                         # Implementation, merge, test, traceability guides
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

The ownership paths above mirror Section 14 of the conception book. Supporting
composition, models, route, and test files stay inside those same documented
top-level areas; there is deliberately no `src/agricultural_advisory/` wrapper.

## Execution model

Every request follows the order required by the conception book:

1. Validate the Mobile question or proactive SMS trigger.
2. Open/update the farmer-crop-plot Crop Passport where identity is available.
3. Build a crop-first Context containing relevant Past, Present, and Future data.
4. Start tree selection at T1, then add or expand T2-T7 from available evidence.
5. Retrieve only rules for `crop_id` and selected trees.
6. Evaluate declarative conditions and record actual/expected evidence.
7. Apply validated hard constraints and data-defined soft penalties.
8. Calculate MobileScore or SMSPriority with neutral configurable weights.
9. Rank deterministically by score, rule priority, then candidate ID.
10. Resolve conflicting candidates and record why the winner was selected.
11. Build one canonical recommendation with reasons, warnings, actions, and references.
12. Persist the complete trace and update the Crop Passport/history.
13. Format/translate/deliver only after reasoning is complete.

Detailed algorithm and file mapping: [`docs/DEVELOPER_1_IMPLEMENTATION.md`](docs/DEVELOPER_1_IMPLEMENTATION.md).

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/v1/advisory/mobile` | Interactive advice for a selected/described crop |
| POST | `/api/v1/advisory/sms` | Generate, format, and simulate proactive SMS delivery |
| GET | `/api/v1/recommendations/{id}` | Retrieve recommendation plus trace |
| GET | `/api/v1/crops` | List crop profiles |
| GET | `/api/v1/crops/{crop_id}` | Retrieve one crop profile |
| POST | `/api/v1/sms/simulate` | Send text to a virtual inbox |
| GET | `/api/v1/sms/inbox/{recipient_id}` | Inspect the virtual inbox |
| GET | `/api/v1/health` | Health status |
| GET | `/api/v1/knowledge/version` | Knowledge version/status metadata |

### Mobile example

```bash
curl -sS -X POST http://127.0.0.1:8000/api/v1/advisory/mobile \
  -H 'Content-Type: application/json' \
  -d '{
    "farmer_id": "farmer-001",
    "crop_id": "irish-potato",
    "question": "How can I improve yield and prepare this plot?",
    "objective": "yield_improvement",
    "region": "West",
    "locality": "Bafoussam",
    "current_stage": "pre-planting",
    "evidence": {
      "soil": {"drainage": "poor"},
      "topography": {"landform": "flatland"},
      "weather": {"rainfall_class": "heavy", "consecutive_rain_days": 3},
      "future": {"month": 8}
    }
  }'
```

### SMS example

```bash
curl -sS -X POST http://127.0.0.1:8000/api/v1/advisory/sms \
  -H 'Content-Type: application/json' \
  -d '{
    "recipient_id": "virtual-phone-001",
    "crop_id": "irish-potato",
    "region": "West",
    "cultivation_period": "August",
    "evidence": {
      "weather": {"rainfall_class": "heavy", "consecutive_rain_days": 3},
      "future": {"month": 8}
    }
  }'
```

## Test and quality commands

```bash
# Complete suite
uv run pytest

# Exclude end-to-end scenarios for a fast loop
uv run pytest -m "not scenario"

# Coverage (gate configured at 85%)
uv run pytest --cov=api --cov=engine --cov=integrations --cov=languages \
  --cov-report=term-missing --cov-report=html

# Formatting and lint
python scripts/check_structure.py
uv run ruff check .
uv run ruff format --check .

# Strict types
uv run mypy

# Validate Developer 2 knowledge
uv run python scripts/validate_knowledge.py knowledge \
  --allow-status draft --allow-status validated

# Standard-library API smoke test (API must already be running)
uv run python scripts/smoke_test.py
```

If a restricted/offline environment already provides Pydantic but cannot install
the test/API packages, the core pipeline can still be checked with:

```bash
PYTHONPATH=. python scripts/self_test.py
```

See [`docs/TESTING.md`](docs/TESTING.md) for layer-by-layer acceptance criteria.

## Configuration

Copy `.env.example` and export the variables through your shell, IDE, container, or
deployment platform. The code reads operating-system environment variables; it does
not automatically parse `.env`, avoiding another runtime dependency.

| Variable | Default | Meaning |
| --- | --- | --- |
| `APP_ENV` | `development` | `development`, `test`, or `production` |
| `APP_HOST` | `0.0.0.0` | Uvicorn bind address |
| `APP_PORT` | `8000` | Uvicorn port |
| `APP_LOG_LEVEL` | `INFO` | Log level |
| `KNOWLEDGE_PATH` | `knowledge` | Section 14 Developer 2 knowledge root |
| `SMS_MAX_LENGTH` | `160` | SMS formatter maximum characters |
| `CORS_ORIGINS` | local ports 3000/8080 | Comma-separated allowed Flutter/web origins |

For production:

```bash
export APP_ENV=production
export KNOWLEDGE_PATH=knowledge
```

In production, only `validated` profiles/rules load. Missing validation therefore
fails safely instead of silently promoting draft agronomy.

## Merge Developer 2 work

Developer 2 should own `knowledge/**` and its agricultural rule tests. The engine
must not receive crop-specific `if/else` code. Before merging:

```bash
git fetch origin
git checkout developer-1-integration
git pull --ff-only
git merge --no-ff origin/developer-2-knowledge
uv run python scripts/validate_knowledge.py knowledge --allow-status validated
uv run pytest
uv run ruff check .
uv run mypy
```

The complete safe procedure, conflict policy, required file layout, acceptance
checklist, and rollback steps are in
[`docs/MERGE_DEVELOPER_2.md`](docs/MERGE_DEVELOPER_2.md).

## Production decisions still open in the conception baseline

- Authentication provider/protocol and RBAC policy.
- Persistent database for contexts, passports, recommendations, traces, and inboxes.
- Real weather, translation, TTS, and SMS providers.
- Developer 2's validated per-crop weights, hard/soft classifications, and sources.
- Retention/privacy policy for farmer context, trace data, and images.
- V2 scheduler, notifications, disease model, and expert escalation channel.

The in-memory repositories are intentional V1 interfaces, not a claim of production
durability. Replace them behind the existing protocols without modifying the engine.

## Troubleshooting

**`uv sync` or `pip install` returns 403 / cannot reach the registry**

Your network or package mirror is blocking the Python index. Configure the approved
corporate mirror or run the Docker build on a network that can access it. The source
itself does not need network access after dependencies are installed.

**`crop profile not found`**

Check `KNOWLEDGE_PATH`, then run `scripts/validate_knowledge.py`. In production,
draft profiles are correctly excluded.

**Every answer warns that weather is unavailable**

This is the safe default adapter. Merge/configure a real `WeatherProvider`, or send
farmer-observed weather in the request; the uncertainty remains explicit.

**Changes in `knowledge/` do not appear**

Restart the V1 process. Knowledge is validated and cached at application startup.

**PowerShell blocks activation**

Use `uv run ...` (no activation needed), or apply your organization's approved
PowerShell execution policy.

## Documentation

- [`docs/DEVELOPER_1_IMPLEMENTATION.md`](docs/DEVELOPER_1_IMPLEMENTATION.md)
- [`docs/MERGE_DEVELOPER_2.md`](docs/MERGE_DEVELOPER_2.md)
- [`docs/TESTING.md`](docs/TESTING.md)
- [`docs/CONCEPTION_TRACEABILITY.md`](docs/CONCEPTION_TRACEABILITY.md)
- [`docs/VALIDATION_REPORT.md`](docs/VALIDATION_REPORT.md)
- [`knowledge/README.md`](knowledge/README.md)
- `docs/reference/Agricultural_Advisory_Architecture_v3_EN.pdf` (source conception book)
