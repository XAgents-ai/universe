# Claude review response — Universe R0.3 collaboration hardening H1

2026-10-17. Evidence first. The patch does **not** change the physics kernel, oracle witness, or claim that intergenerational physical inheritance has been demonstrated.

## Findings / dispositions

| Item | Disposition | Exact evidence |
|---|---|---|
| T2 plaintext bearer token in persistent journal | **Initial patch + passing local regression** | `open_world.py`, `test_journal_integrity.py::test_token_not_persisted` |
| R3 step mutates world before journal fsync | **Initial patch + passing failure-injection regressions** | `test_step_commit_failure_is_atomic`, `test_join_commit_failure_is_atomic`, `test_disk_commit_failure_poisoned` |
| R2 torn journal tail | **Initial patch + passing local regressions** | `test_torn_tail_recovered_complete_records_preserved`, `test_completed_tamper_is_rejected` |
| Workflow PR secret exfiltration risk | **Review jobs changed to owner-dispatched trusted checkout; no PR-code execution** | `.github/workflows/*-review.yml`, `scripts/fetch_review_context.sh`, `scripts/test_workflow_boundaries.py` |
| Codex editing workflow / validator | **Guarded with trusted pre-model validator copy, expanded denied paths** | `scripts/validate_agent_changes.py`, locally tested malicious workflow + validator edit |
| CI required, AI reviews advisory | **Documentation and triggers updated; GitHub ruleset still owner action** | `docs/GITHUB_SETUP.md`, `.github/workflows/ci.yml` |
| AI reviewer quotes CI evidence | **Review packet tries exact-head CI run + real artifact; unverified/absent is explicitly marked** | `scripts/fetch_review_context.sh`. Hosted GitHub API behavior remains **UNTESTED**. |
| Acceptance criteria authored by owner/reviewer | **Issue drafts and governance written, but not GitHub policy enforced** | `docs/issues/`, `AGENTS.md`, `CLAUDE.md` |
| W1 world-owned batched clock | **OPEN, specified as issue** | `docs/issues/01-world-clock.md`; current world remains call-to-tick |
| F7/F8 oracle grammar / depth-7 bounded negative | **OPEN, issue drafted** | `docs/issues/02-oracle-evidence.md`; earlier negative numbers not reused as new proof |
| F10/F11 full gated responder | **OPEN, acceptance strengthened** | `docs/issues/03-gated-responder.md` |

## Practical remaining security blockers before live credentials

- The first-party GitHub actions are SHA-pinned to known release refs; verify upstream references on GitHub after bootstrapping.
- **`anthropics/claude-code-action@v1` and `openai/codex-action@v1` are still unpinned.** Owner must review and replace with verified full commit SHAs before enabling model secrets.
- GitHub private remote is **not** created; no actual hosted workflows, pull requests, authenticated bots, CI artifact retrieval or branch rules have been tested.
- CI from a PR runs its candidate Python with **no model credentials**. Secret-backed review/implementation runs checkout trusted default-branch code. Untrusted prompt injection is still possible; no claim of full isolation.
- Journals from historical R0.3 versions may contain plaintext tokens. Do not reuse these or retroactively declare them confidential. Rotate credentials, begin a fresh journal, keep old evidence access-restricted.
- Local LiveUniverse uses an in-process lock. Multiple Uvicorn workers / server instances sharing one journal are not supported; explicit cross-process locking and deployment security are pending.
- The durable-append scheme was failure-injection tested, but not power-loss tested on multiple filesystems. Interrupted fsync requires restart and journal verification.
- The system has not run Claude or Codex with real provider credentials in this environment.

## Reviewer instructions

1. Run `bash run_checks.sh` and `python scripts/test_workflow_boundaries.py` on an isolated developer machine.
2. Adversarially inspect `open_world.py` transaction boundaries, hash-based bearer lookup, torn-tail behavior and server actor endpoints.
3. Inspect all `.github/workflows/*.yml`, `scripts/bootstrap_github.*`, `scripts/validate_agent_changes.py`, and `scripts/fetch_review_context.sh` before the owner runs bootstrap.
4. Challenge whether PR code or untrusted text can access model secrets, whether preflight can be bypassed, and whether CI observations come from the exact PR commit.
5. Do not mark W1, F7/F8, F10/F11, or the multi-generation ratchet as established.

## Local results

- `bash run_checks.sh`: exit 0 on local container (Python environment; full output `docs/evidence/HARDENED_CHECKS.txt`).
- Static workflow policy checker: pass.
- Protected-path validator self-tamper/workflow-tamper simulation: rejected.
- ZIP packaging and integrity separately verified.

Model review comments are advisory. Physics CI must be required by the repository owner; no hosted GitHub branch protection is assumed to exist.
