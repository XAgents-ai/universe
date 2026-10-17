# Setup the shared Universe repository under your account

The package is **local and prepared**. A private GitHub repository does not yet exist until you authenticate on your computer and run the bootstrap. ChatGPT and Claude are separate account sessions: GitHub plus workflows is the shared coordination surface.

## 1. Create your private repo

Install [GitHub CLI](https://cli.github.com/). Sign in using `gh auth login` (browser flow; **do not paste credentials into any AI chat**). In the extracted project directory:

```bash
bash scripts/bootstrap_github.sh universe
```

On Windows, you can instead run from PowerShell in the extracted project directory:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap_github.ps1 universe
```

This initializes Git, commits tracked source, creates a **private** GitHub repository named `universe` in your GitHub account, sets `origin`, and pushes the baseline. If a remote already exists it refuses to overwrite it. You can instead connect ChatGPT's GitHub plugin, then work directly with repository content after its connection is confirmed.

## 2. Protect main before enabling model automation

In Settings → Rules → Rulesets (or Branch protection), require pull requests and human review; set **Physics and Replay CI / acceptance (3.11)** and **acceptance (3.13)** as required checks after an initial PR generates the exact check names. AI reviews are **advisory**, never required/veto checks. Block force pushes, deletions, and any bot bypass of human review. Enforcement for private repositories varies by plan: verify that the rule is actually active before trusting it.

All secret-backed AI review workflows in this version are **manually dispatched on trusted default-branch code**. They retrieve the PR diff as untrusted text; no PR checkout or PR code execution occurs in their secret-backed jobs. Independent CI remains automatic on PRs but has **no model API keys**.

**Supply-chain review before secrets:** The four core GitHub-maintained actions in CI and review workflows are SHA-pinned. Anthropic's and OpenAI's model actions remain tagged `@v1`; **verify and replace those tag references with full immutable commit SHAs before enabling model API secrets**. A dispatched model job now fails before its model action when any required action reference is not a 40-character SHA; CI warns without blocking repository bootstrap. Inspect upstream action source and make sure the referred revision is appropriate. AI prompts can still be influenced by malicious diffs; manual triggering, read-only execution, and limited GitHub permissions reduce risk but do not establish absolute isolation. Do not enable this on third-party fork PRs.

## 3. Configure account-owned model credentials

Set `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` in Settings → Secrets and variables → Actions → Repository secrets, **only after pinning and reviewing the action implementations**. Chat subscriptions are not transferable API access. Set provider budgets. Never paste keys in chat, issue body, or git. Keep the repository private initially. Do not enable model-backed workflows until budget and branch rules are confirmed.

## 4. Explicit, advisory collaboration

Enable repository variable `ENABLE_AI_REVIEWS=true` to allow owner-dispatched reviews. Go to **Actions → Codex Advisory PR Review** or **Claude Advisory PR Review**, click **Run workflow**, and enter the PR number. Each reads the trusted default branch plus an untrusted diff; it records the exact-head CI run URL/status and available test-output artifact. Codex posts a review comment; Claude publishes its review through the action's execution report. These comments and reports do **not** approve PRs.

For Codex implementation, first set repository variable `ENABLE_CODEX_IMPLEMENT=true` **after** pinning the action and setting branch protections, then manually trigger **Actions → Codex Implement Scoped Issue**, enter a preapproved issue ID with reviewer/owner-authored acceptance criteria. A protected-path validator copied before the model runs rejects workflow, governance and CI entrypoint changes. **Do not run model-generated tests/code in the same secret-backed job**: the implementation job opens the PR, and the separate no-model-secrets CI then runs its code. A separate human reviewer must still inspect the complete diff. The model proposes a PR; it never merges it.

Optional Claude issue investigation is manually dispatched and disabled by default (`ENABLE_CLAUDE_ISSUES=false`). It is read-only and cannot publish a PR. Leave it disabled until independently tested; use your connected Claude coding session for implementation instead. Do not treat an issue label or model-authored acceptance text as owner approval.

**CI evidence:** PR changes are tested without model secrets. Preserve test logs as action artifacts and require the exact SHA; reviewers should quote those logs (or declare them absent) rather than infer results from the PR description.

## 5. Seed the initial engineering issues

After authenticating and pushing, run:

```bash
bash scripts/seed_issues.sh
```

This creates the scoped initial roadmap issues only when no issue with the exact title is found. They are not claims of completed science.

## 6. Validate the setup

Create a small PR with a new regression test. Confirm CI on it and then manually dispatch separate Claude/Codex reviews when enabled. Check that neither model merged the branch and that your branch rule requires an independent approval. Close the test PR without merging if preferred.

## What remains manual

Only account-owning actions: GitHub login, initial private remote creation, storing keys, selecting spending limits and GitHub branch protections. Model orchestration, evidence collection, PR reviews and test execution can then occur on the repository. The universe server remains local until a separate security/deployment project is approved.

**Checkout-token boundary:** Codex implementation uses `persist-credentials: false`. Its only `gh` calls receive step-scoped `GH_TOKEN`; Git authentication is installed by `gh auth setup-git` only in the trusted publication step *after* the copied validator has approved candidate paths. Avoid replacing the checkout settings without security re-review.
