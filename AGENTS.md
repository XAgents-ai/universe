# Universe V0 — Coding-agent contract

This repository contains a small reproducible digital physical substrate, NOT a simulation of sentient life. The primary rule is **observable physical state, not agent narration**.

## Working protocol

- Read `README.md`, `UNIVERSE_V0_PHYSICS_SPEC.md`, and `docs/SCIENTIFIC_CLAIMS.md` before making claims.
- Keep experimenter-only `env_ops` separate from participant `set`, `observe`, `claim`, `wait`. No `create_machine`, world edits, direct participant communication, or energy exemptions.
- Preserve the deterministic tick phases, conservation accounting, authority rules, reproducible state hashes, and replay semantics.
- A discovered mechanism is a **witness** only when a legal action trace builds it and a separate functional test exercises it after agent disconnection.
- Do not convert bounded-search failure into an impossibility proof. Distinguish canonical cold search from seeded production dynamics.
- Report what changed, the falsifier, tests run, their exact results, and untested claims in every PR.
- Add a regression test reproducing a discovered bug *before* fixing the bug where practical.
- Never merge your own PR or weaken test gates. Do not modify `.github/workflows/**` unless explicitly requested by the human owner.
- Never read, print or commit `.universe_state/`, local API tokens, or key files. Do not publish the participant journal; it can contain private tokens.
- Avoid claims that models are conscious or that the world has demonstrated emergence, life, or cumulative evolution.

## Verification

`bash run_checks.sh` is the current deterministic acceptance suite. Browser tests are optional and require Chromium/Playwright; read `README.md`.

## Division of labor

Models can implement or review. Independence comes from a separate reviewer producing counterexamples and tests, not from a model's identity. GitHub CI is authoritative for mechanical invariants; scientific interpretation remains a human-reviewed claim.


### Security/evidence gate

Do not propose editing `.github/workflows/`, `run_checks.sh`, `AGENTS.md`, `CLAUDE.md`, bootstrap scripts, `docs/SCIENTIFIC_CLAIMS.md`, or credential files in an autonomous implementation run. Acceptance criteria belong to the owner/independent reviewer and are frozen before issue assignment. Do not assert new scientific claims without an executable test ID in required CI. AI reviews are advisory; quote actual exact-commit CI output or state it was absent.
