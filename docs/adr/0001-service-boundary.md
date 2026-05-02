# ADR-0001: Service boundary — Plugin Modular Monolith vs Microservices

- **Status:** Accepted
- **Date:** 2026-05-02
- **Deciders:** JS-RE-Bench maintainers (informed by codex backend architect)

## Context

The platform must evaluate LLMs across 18 reverse-engineering dimensions. A
naive split into 18 microservices was considered. Each dimension shares
sample storage, metric computation, scheduler state, evidence chains, and
report generation, so service-per-dimension creates duplication and adds
operational cost.

## Decision

Adopt a **Plugin Modular Monolith + Isolated Workers**:

- A single FastAPI control plane orchestrates runs.
- Each dimension is a Python plugin behind `BaseDimension` / `BaseChallenge`
  / `BaseEvaluator` / `BaseMetric` contracts.
- Untrusted execution (JSVMP, anti-debug probes) runs in **Docker
  sandboxes** launched by Celery workers — the only true service boundary.
- Multi-LLM access funnels through `ModelAdapter` ports.

## Consequences

**Pros:**
- One repo, one deploy, one DB schema = simpler CI, simpler Q1 compliance.
- Shared evidence model gives Q9/Q10 a coherent foundation.
- New dimensions ship as a directory + plugin, not a service.

**Cons:**
- Resource isolation between dimensions is logical, not physical.
- Scaling beyond a single host requires moving Celery workers / Postgres.

If the project grows beyond a single team, the natural next step is to
split `sandbox-runner` and `llm-broker` into dedicated services, retaining
the plugin contracts. This evolution path is documented in ADR-0006 (TBD).
