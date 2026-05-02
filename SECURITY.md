# Security Policy

## Reporting a Vulnerability

**Do NOT open a public issue for security vulnerabilities.**

Email security@js-re-bench.org with:

- Description of the vulnerability
- Steps to reproduce
- Affected versions
- Potential impact

We will acknowledge within 48 hours and aim for a fix within 7 days.

## Scope

This policy covers the JS-RE-Bench platform codebase. It does **not** cover:

- LLM API keys or credentials misused by users
- Third-party dependencies (report to upstream)
- Samples uploaded by contributors (handled separately)

## Secure Development

- All PRs pass `pre-commit` hooks (ruff, mypy)
- Dependencies are pinned in `pyproject.toml`
- Sandbox code runs in isolated Docker/Node vm.Script contexts
- No secrets are committed (enforced by `.gitignore` and `detect-private-key` hook)
