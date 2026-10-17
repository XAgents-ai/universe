# Security and deployment boundary

Universe R0.3 is a **local scientific prototype**, not a public multi-tenant service. Do not expose `server:app` on the public Internet. Its persistent JSONL journal contains live participant resume tokens. Do not commit, upload, paste or publish `.universe_state`.

All agent-issued operations must pass through the production `AgentBoundary`, not the experiment-only boundary. Use isolated clones for experimenter `drop`, `remove`, `replace`. GitHub model review workflows are opt-in: configure API keys only as encrypted GitHub Actions secrets. Run code tests in separate jobs without these keys. Enable branch protection and require independent review before merging.

Known limitations inherited from R0.3 include local HTTP without TLS, rate limiting, identity infrastructure, hardened token storage, transactional journaling, tamper signatures or public threat-model coverage. Report security weaknesses by private repository issue; do not share exploit tokens publicly.

## Collaboration workflow security (patch 2026-10-17)

Secret-backed PR reviews are manually dispatched and use trusted-base checkout; untrusted diff and CI traces must never be executed in those jobs. Pin `anthropics/claude-code-action` and `openai/codex-action` to reviewed SHAs before activating. `codex-implement` uses a pre-model trusted validator and cannot modify `.github/`, trusted CI launchers, or governance documents in its proposed PR. The secret-backed implementation job **does not run generated code/tests after Codex**; separate PR CI runs with no model secrets. This check is a preflight, not a sandbox or replacement for branch protection.

## Journal privacy/recovery

R0.3 collaboration patch stores SHA-256 token digests (tokens have 256 random bits), not plaintext bearer tokens. New join tokens are returned only once over HTTP. Existing R0.3 journals containing raw bearer tokens must be retired, and all previously exposed tokens rotated; these historical logs cannot be treated as confidential retroactively. Transitions stage on clones and become live only after an fsynced append; if append/fsync fails, the process stops accepting writes until restarted and replayed. Unterminated last fragments are discarded, but complete corrupt records fail closed. This is not yet proof of cross-filesystem power-loss durability or production-safe public deployment.

**Single-process limitation:** The journal writer uses a process-local lock; starting multiple Uvicorn workers sharing `UNIVERSE_STATE_DIR` is unsafe. Use one local worker only. Do not expose this prototype on a public network.
