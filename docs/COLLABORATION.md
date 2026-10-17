# Two-model collaboration contract

**Shared artifact:** one private GitHub repository. This repo, including its version-controlled issue/PR review history, is the source of truth. Chat transcripts alone are not decisions.

**Workflow:** create a scoped issue with an observed gap and falsifier. One developer (Codex, Claude, or human) submits a branch and PR. Independent reviewer examines the diff and supplies reproducible counterexamples. CI runs deterministic checks in a job with **no model API credentials**. Owner decides whether scientific claims changed; only authorized maintainers merge.

## Authorization boundaries

- **Codex implementation:** opt-in `ENABLE_CODEX_IMPLEMENT=true` and explicitly owner-triggered GitHub Actions workflow (`Codex Implement Issue`) reading an issue, editing a branch, and opening a PR; it must not merge.
- **Claude PR review:** manually dispatched from the trusted default branch when `ENABLE_AI_REVIEWS=true` and `ANTHROPIC_API_KEY` is configured. Designed for write-access contributors' branches within the private repository.
- **Codex PR review:** manually dispatched and advisory; GitHub Action uses a read-only permission profile. Feedback is posted as PR comment by a separate GitHub job.
- **Claude issue investigation:** optional maintainer-dispatched *read-only* workflow enabled only with `ENABLE_CLAUDE_ISSUES=true`. It does not create commits or pull requests. A write-capable Claude development workflow requires a separate validated publication job and further threat review. Until then, Claude can develop through its separately authorized local or connected coding environment.
- **All external model credentials:** GitHub Actions secrets, *never* files/issue text.
- **Runtime agent credentials:** `.universe_state` is sensitive, ignored, and must never become CI test data or be committed.

## Evidence contract for each PR

1. The claim being made and the competing hypothesis.
2. Reproduction instructions and the exact initial world and seeded inputs.
3. Before/after tests, signed or hashed logs when applicable.
4. Full list of test commands executed and failures/timeouts.
5. Whether the result is a new O1 functional witness, an O2 legal construction witness, or a broader inheritance experiment.
6. Any limits on extrapolation (seed/sample size, cold-versus-production physics, bounded search, unmodeled effects).

Neither model may approve or merge its own changes. A green workflow means its scripted checks passed; it does not certify the universe's scientific claims.

## Security caveats

Private GitHub is not a production secret vault. GitHub Actions third-party model agents receive selected repository context and may incur API fees. Keep workflows opt-in until credentials, billing, branch protection, and maintainer access are reviewed. Avoid running model-backed jobs on forks or untrusted PRs. Model suggestions are untrusted until reproduced.

## Separation of responsibility and CI evidence

The **owner or independent reviewer** writes issue acceptance criteria before an implementer is assigned. Implementers cannot certify their own acceptance tests. Physics CI is a required check; model reviews are advisory and must never veto or approve a PR. PR reviewers must use the actual exact-head CI run and quote the real run output or explicitly note that it was unavailable.

Credentialed review jobs always checkout the trusted base; PR diffs and CI artifacts enter solely as **untrusted data**, not executable code. Reviews are explicit `workflow_dispatch` calls, not automatic secret-backed `pull_request` jobs. No reviewer has commit permission. These safeguards reduce but cannot eliminate prompt injection or third-party action risks; action pins and human approvals are prerequisites for credential setup.

## Clarification: what the AI reviewers execute

Advisory PR review workflows **do not execute proposed PR code**. Their jobs use model API credentials and only read a trusted-base checkout plus PR diff and exact-head CI logs as untrusted data. **Physics and Replay CI**, run without model keys, executes the actual proposed code. A human reviewer can separately run tests in a disposable environment. Do not present a model-generated review comment as proof that the reviewer executed tests.
