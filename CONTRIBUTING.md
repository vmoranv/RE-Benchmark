# Contributing to JS-RE-Bench

We welcome contributions across **dimensions**, **metrics**, **samples**,
**adapters** and **documentation**. This guide focuses on the recurring
extension flow rather than corporate boilerplate.

## Project layout (TL;DR)

| Path | What lives here |
|------|-----------------|
| `benchmark/core/abstractions/` | ABC contracts you implement against |
| `benchmark/core/adapters/` | Concrete LLM / artifact / quota adapters |
| `benchmark/core/orchestration/` | State machine, scheduler, default evaluator |
| `benchmark/core/persistence/` | SQLAlchemy models + Alembic migrations |
| `benchmark/dimensions/dimNN_*/` | Per-dimension plugin packages |
| `benchmark/metrics/{common,specialized}/` | 6 + 9 metric calculators |
| `benchmark/challenges/qNN_*/` | Q1 – Q12 qualification challenge implementations |
| `apps/{api,cli,worker,mcp_server}/` | Entry points |
| `frontend/` | React + Vite UI |
| `tests/{unit,integration,determinism}/` | Test layers |
| `docs/adr/` | Architecture decision records |

## Adding a new dimension

1. `cp -r benchmark/dimensions/dim01_deobfuscation benchmark/dimensions/dimXX_<short_name>`
2. Update `code`, `name`, `paper_refs`.
3. Edit prompts in `prompts/round{1,2,3}.j2`.
4. Implement `objective_check` against your sample's ground truth.
5. Pick or implement metrics under `benchmark/metrics/specialized/` if needed.
6. Add seed samples under `benchmark/samples/seed_samples/DXX/` plus a
   `manifest.yaml` describing source, level, obfuscator, semantic test
   cases.
7. Write at least one unit test covering `parse_response` and one covering
   `objective_check` happy + unhappy paths.
8. Run `make test lint typecheck`.
9. Open a PR. CI runs unit / determinism / Q1 smoke automatically.

## Adding a new model adapter

1. Subclass `ModelAdapter` under `benchmark/core/adapters/model/`.
2. Set `model_id` and a `ModelCapabilities` class variable.
3. Implement `async def send(...)` mapping the unified contract to vendor SDK calls.
4. Surface degraded features (no seed, no JSON schema, etc.) in
   `capabilities` rather than silently dropping inputs.
5. Add a unit test using a mocked HTTP client.

## Coding standards

- Python: `ruff` + `black` (line length 100), mypy strict.
- Type hints everywhere; no `Any` in public APIs.
- Pydantic v2 models for I/O boundaries.
- TypeScript: ESLint flat config; no implicit `any`.

## Testing

- Unit tests must run without Docker / DB / network.
- Integration tests may use `services:` in `ci.yml` (PG / Redis already wired).
- Determinism tests must be byte-identical across runs (no clocks, no UUIDs).

## Commit messages

Follow Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`).
Reference dimension or challenge codes when relevant: `feat(D02): add unknown-opcode evaluator`.
