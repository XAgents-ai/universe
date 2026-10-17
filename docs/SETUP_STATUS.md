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
