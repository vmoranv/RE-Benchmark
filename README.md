# JS-RE-Bench

> **JS/Web Reverse Engineering Comprehensive Benchmark Platform**
>
> Extending [JsDeObsBench](https://arxiv.org/abs/2406.06636) into a unified, public, reproducible benchmark covering the full Web/JS reverse-engineering pipeline.

[![CI](https://github.com/js-re-bench/js-re-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/js-re-bench/js-re-bench/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Overview

JS-RE-Bench evaluates LLMs and tools across 18 reverse-engineering dimensions:
deobfuscation, JSVMP unpacking, TLS fingerprinting, WASM/SourceMap recovery,
anti-debug bypass, hook quality, Canvas/WebGL, V8 internals, native instrumentation,
Android WebView, syscall correlation, protocol inference, memory scanning,
trace replay, cross-domain evidence, HTTP proxy, obfuscator correctness,
LLM semantic probing.

It is built around three pillars:
- **15 quantitative metrics** (6 general + 9 specialized including `M8` semantic fidelity, `M9` LLM decay rate)
- **12 qualification challenges** (Q1-Q12) executed automatically in CI
- **5-tier obfuscation taxonomy** (L1 lexical through L5 virtualization)

## Quick Start

### Prerequisites

- [uv](https://docs.astral.sh/uv/) package manager
- Python 3.11+ (managed by uv automatically)
- Node.js 22+ (for sandbox-based semantic test execution)
- Docker 24+ and Docker Compose v2 (for full stack deployment)

### Development Setup

```bash
# 1. Clone and enter the repo
git clone https://github.com/js-re-bench/js-re-bench.git
cd js-re-bench

# 2. Install Python dependencies (creates .venv automatically)
uv sync

# 3. Install pre-commit hooks (ruff, mypy, format checks)
uv run pre-commit install

# 4. Verify everything works
uv run pytest -v                    # 31 tests should pass
uv run pre-commit run --all-files   # All hooks should pass

# 5. Run the CLI
uv run bench version                # Print version
uv run bench dimensions list        # List all 18 dimensions
uv run bench samples list           # List loaded samples for D01
```

### Expected Results

After `uv sync && uv run pre-commit install`:
- `uv run pytest` — 31 passed, 0 failed
- `uv run pre-commit run --all-files` — 9 hooks, all Passed
- `uv run bench dimensions list` — Rich table with 18 dimensions
- `uv run python -c "from apps.api.container import get_dimension_registry; r = get_dimension_registry(); print(len(r))"` — prints `18`

### Running a Benchmark

```bash
# Mock model (deterministic, no API key needed)
uv run bench run --dimension D01 --execute

# With Anthropic Claude (requires ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=sk-ant-...
uv run bench run --dimension D01 --model anthropic/claude-sonnet-4-6 --execute

# With OpenAI GPT (requires OPENAI_API_KEY)
export OPENAI_API_KEY=sk-...
uv run bench run --dimension D01 --model openai/gpt-4o --execute
```

### Docker Deployment (Q1 Headless Reproducibility)

```bash
docker compose -f infra/compose/docker-compose.yml up --abort-on-container-exit
```

The stack exposes:
- **API**: http://localhost:8000 (Swagger at `/docs`)
- **Frontend**: http://localhost:5173
- **Postgres**: localhost:5432
- **Redis**: localhost:6379

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/dimensions` | List all 18 dimensions |
| POST | `/api/v1/runs` | Submit a benchmark run |
| GET | `/api/v1/runs` | List runs |
| GET | `/api/v1/runs/{id}` | Get run details |
| GET | `/api/v1/reports/{id}/json` | Export run as JSON |
| GET | `/api/v1/reports/{id}/csv` | Export run metrics as CSV |
| GET | `/api/v1/reports/batch/json` | Batch export filtered runs |

## Architecture

JS-RE-Bench follows a **Plugin Modular Monolith + Isolated Workers** design:

```
CLI / REST API
       |
  FastAPI Control Plane
    |              |
PostgreSQL      Redis
    |              |
Artifact CAS   Celery Workers
                  |
            Docker Sandbox Pool
        (jsvmp-node / browser-anti-debug)
```

Key design decisions documented in `docs/adr/`:
- ADR-0001: Plugin Modular Monolith over Microservices
- ADR-0002: Engine vs Model Determinism Separation

## Supported Models

| Provider | Model ID Format | Example |
|----------|----------------|---------|
| Mock (deterministic) | `mock/*` | `mock/echo-v1` |
| Anthropic | `anthropic/*` | `anthropic/claude-sonnet-4-6` |
| OpenAI | `openai/*` | `openai/gpt-4o` |

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines. Pre-commit hooks enforce code quality automatically.

## Citing

If you use JS-RE-Bench in academic work, please cite via [`CITATION.cff`](./CITATION.cff).

## License

Apache License 2.0 — see [`LICENSE`](./LICENSE).

## Acknowledgements

Inspired by JsDeObsBench, JSIMPLIFIER (NDSS 2026), OBsmith (OOPSLA 2026), CASCADE (ICSE SEIP 2026), and *The Code Barrier* (arXiv 2504.10557).
