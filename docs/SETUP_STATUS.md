# Setup status at handoff — 2026-10-17

## Locally verified

- Imported **R0.3** physics and oracle intact. **Journal code and collaboration workflows are modified by the H1 hardening patch**; consult `docs/reviews/CLAUDE_HARDENING_RESPONSE.md`.
- `bash run_checks.sh` returned exit code 0 after journal hardening; complete local output is `docs/evidence/HARDENED_CHECKS.txt`, historical baseline in `docs/evidence/BASELINE_CHECKS.txt`.
- YAML syntax and static workflow boundaries validated locally for five GitHub Actions workflows. **Hosted workflows have not been exercised.**
- Verified no `.universe_state` runtime journal was copied into the repository.
- Coding-agent task-prompt generator exercised on a synthetic issue.
- Repository prepared as local Git source; Github-hosted workflows have NOT yet been run.

## Not yet performed — requires owner's authenticated account

- Create private remote repository in owner's GitHub account.
- Configure branch protection / rulesets.
- Add `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` (or Anthropic's supported alternative) as secrets.
- Review and SHA-pin model actions before adding secrets; then explicitly opt in to `ENABLE_AI_REVIEWS=true` and optional `ENABLE_CLAUDE_ISSUES=true` for manual dispatch.
- Test hosted model review and Codex-created PR workflow; their runtime behavior is **not** asserted to pass before these steps.

## Research claims deliberately not made

No 3D physics, emergent life, full gated responder construction, external LLM interoperation, or cumulative intergenerational ratchet has been demonstrated. The baseline's smaller physical responder, canonical-cold bounded oracle, and live-world interface have the evidence limits listed in `docs/SCIENTIFIC_CLAIMS.md`.

## Governance patch G2 (2026-10-17)

Claude's G1–G4/G6 patch applied. Additional guard: Codex checkout cannot persist GitHub credentials into the model step; the push step authenticates after validation. Credentialed model actions fail closed on mutable action tags; Codex implementation requires a separate opt-in variable. Claude's optional issue workflow is restricted to read-only investigation. Existing work remains local until owner creates a private remote. No GitHub-hosted tests have run.

## GitHub setup (2026-10-17, Neo for Zero)

This section is added after the G2 drop. `docs/evidence/G2_MANIFEST.sha256` still records the drop as delivered, so the four workflow files edited here no longer match it. That is expected.

1. **Private remote: done.** `https://github.com/varinderpratap/universe`, private, default branch `main`. The baseline commit holds the drop byte for byte.
2. **Branch protection: not possible on this plan.** `GET /repos/varinderpratap/universe/branches/main/protection` returned HTTP 403: "Upgrade to GitHub Pro or make this repository public to enable this feature." The account is on GitHub Free. Until that changes, nothing on GitHub enforces PR-only merges, required checks or blocked force pushes on `main`.
3. **Model actions pinned to immutable SHAs, resolved through the GitHub API on 2026-10-17:**
   - `anthropics/claude-code-action@f27be6b65a4652f08a2ba3cff79114829b588967`, release `v1.0.252` (also what `v1` pointed at that day).
   - `openai/codex-action@bdf19a4a223ec2549a3e2274a0cf61556bc07675`, tag `v1.13` (also what `v1` pointed at that day).
   - `scripts/require_pinned_model_action.py` prints PASS for all four workflows. `scripts/test_workflow_boundaries.py` passes.
   - A pin is not a source review. A source review of both SHAs (2026-10-17) found both genuine: official orgs, SHAs on each repo's main history, every input these workflows use present in `action.yml`, no open advisory against either.
   - That review found two gaps, now closed. (a) Without `github_token`, claude-code-action exchanges OIDC for a Claude App token with contents, pull-requests and issues write, whatever the workflow's `permissions:` say. Both Claude workflows now pass `github_token: ${{ github.token }}`. (b) codex-action installs `@openai/codex@latest` when `codex-version` is empty. Both Codex workflows now pin `codex-version: '0.163.0'`, which was npm `latest` on 2026-10-17; the proxy package exists at the same version.
   - Not checked by that review: whether codex-action's `dist/main.js` matches its `src/`; the telemetry of the Claude Code and Codex CLIs; the checksums Bun and Codex binaries get at download.
4. **Model credentials: not set.** They are the owner's: API keys, provider spending limits, then `gh secret set`. `ENABLE_AI_REVIEWS`, `ENABLE_CODEX_IMPLEMENT` and `ENABLE_CLAUDE_ISSUES` are left unset, so every model workflow stays off.
