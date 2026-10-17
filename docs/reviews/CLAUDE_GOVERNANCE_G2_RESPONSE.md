# Governance G2 — response to Claude's H1 review

Date: 2026-10-17. **This is a locally tested proposal, not an authenticated GitHub deployment.**

## Patch disposition

- **G1 (Codex inherited write token): closed for checkout/step-scoping.** Removed job-level `GH_TOKEN`; model step receives no `GH_TOKEN` from that job. Added `persist-credentials: false` to the Codex checkout. `gh auth setup-git` is invoked only in the trusted post-validator publication step that has a step-local `GH_TOKEN`. Codex issue workflow is now opt-in via `ENABLE_CODEX_IMPLEMENT=true`.
- **G2 (Claude issues lacked trusted validator): applied the supplied stage-before/validate-after patch.** Further reduced job permissions to `contents/issues/pull-requests: read`. It is now explicitly an *investigation-only*, nonpublishing workflow. Leave `ENABLE_CLAUDE_ISSUES` off; use a separately authorized Claude coding session until a safe publisher is designed.
- **G3 (acceptance and trusted scripts mutable): closed for named protected paths, broadened to `scripts/` as a whole** so newly created scripts cannot become unreviewed governance. Protected `docs/issues/`, `docs/evidence/` and requirements. Added a disposable-Git test that proves the validator refuses protected changes but accepts a scoped experiment edit.
- **G4 (mutable `@v1` action references): execution now fails closed.** A trusted-base preflight refuses a model action unless its workflow references exactly one 40-character hexadecimal commit SHA. The existing `@v1` references have deliberately *not* been guessed or changed; consequently **none of the model workflows can execute successfully until the owner verifies and pins the upstream commits**. CI prints warnings without blocking initial bootstrap.
- **G6:** the GitHub PR body now uses `printf` for proper newlines.
- **J1:** added session-auth-versus-person-identity to the actor threat-model issue, without pretending the bearer token proves human/model identity.
- **F7:** the gated responder's pre-approved O2 acceptance now explicitly requires labeling the input model.

## Actual local evidence

- `bash run_checks.sh`: exit 0; 35 `PASS`-prefixed lines; test transcript in `docs/evidence/G2_LOCAL_CHECKS.txt`.
- `python scripts/test_workflow_boundaries.py`: pass with named warnings for **four** unpinned model references.
- `python scripts/test_protected_path_validator.py`: 5/5 cases behave as expected (four rejected edits, one accepted experiment edit).
- `python scripts/audit_repository.py`: pass; no private `.universe_state` directory in the exported repository.
- YAML parser successfully read all five workflows. **No GitHub Actions execution or authenticated push has taken place.**

## Residual risks — do not overclaim

1. **Publication still shares a job/checkout with the Codex implementation.** While credentials do not persist into the model step, a hostile code-writing agent could alter untracked Git metadata or hooks outside the path validator's tracked-diff checks. The publish step must eventually run in a **fresh trusted checkout in a distinct job** with a separately validated patch artifact. Until that split is implemented and independently verified, leave `ENABLE_CODEX_IMPLEMENT` **unset/false**. The source and acceptance gate can be pushed privately, but do not activate automatic code writing yet.
2. A 40-hex action reference is immutable but not inherently trustworthy. The account owner must establish that it is a vetted upstream commit before enabling credentials. `@v1` remains a deliberate deployment blocker.
3. Read-only Claude issue workflow may not produce a useful contribution if its third-party action expects write permissions. It is intentionally disabled; no hosted behavior is claimed.
4. GitHub-hosted check names, ruleset enforcement on the owner's plan, official action compatibility, and model-token security have not been validated in the owner's GitHub account. Branch protection and actual CI must be verified there.
5. W1 (world clock), F7/F8 (oracle input/exhaustion), and F10/F11 (gated responder) remain separate scientific issues. G2 does not modify the physics kernel.

## Owner's next safe step

Review `scripts/bootstrap_github.sh` or `.ps1` and `docs/GITHUB_SETUP.md`, then authenticate with GitHub CLI and create the private `universe` repository. **Do not add model API keys or enable write-capable AI jobs yet.** Require secret-free physics CI on pull requests, then give Claude and ChatGPT the same `owner/universe` repository reference through approved account connections.
