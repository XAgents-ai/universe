"""Static policy checks; not a replacement for hosted workflow security tests."""
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
W=ROOT/'.github/workflows'
ci=(W/'ci.yml').read_text()
assert '${{ secrets.OPENAI_API_KEY }}' not in ci and '${{ secrets.ANTHROPIC_API_KEY }}' not in ci
assert 'pull_request:' in ci and 'run_checks.sh' in ci
for f in ['claude-review.yml','codex-review.yml']:
    body=(W/f).read_text()
    assert 'workflow_dispatch:' in body and 'pull_request:' not in body
    assert "ENABLE_AI_REVIEWS == 'true'" in body
    assert 'fetch_review_context.sh' in body
    assert 'ref: ${{ github.event.pull_request.head.sha }}' not in body
    assert 'actions/checkout@' in body
impl=(W/'codex-implement.yml').read_text()
assert 'trusted_validator.py' in impl and 'scripts/validate_agent_changes.py "$RUNNER_TEMP/trusted_validator.py"' in impl
assert 'bash run_checks.sh' not in impl, 'Model-generated code must not run in secret-backed implementation job'
import re
unpinned=[]
for f in ['claude-review.yml','codex-review.yml','claude-issues.yml','codex-implement.yml']:
    for m in re.finditer(r'uses:\s*(anthropics/claude-code-action|openai/codex-action)@(\S+)',(W/f).read_text()):
        if not re.fullmatch(r'[0-9a-f]{40}',m.group(2)): unpinned.append(f'{f}: {m.group(1)}@{m.group(2)}')
if unpinned: print('WARNING unpinned model actions (pin a verified commit SHA before enabling AI workflows):',*unpinned,sep='\n  ')
issues=(W/'claude-issues.yml').read_text()
assert 'trusted_validator.py' in issues, 'claude-issues must stage and run the trusted validator like codex-implement'
assert '\n      GH_TOKEN:' not in (W/'codex-implement.yml').read_text().split('steps:')[0], 'GH_TOKEN must be step-scoped, not job-scoped, in the implementation job'

# G1b: checkout must not persist a write credential in the Codex workspace.
assert 'persist-credentials: false' in impl.split('Preserve a trusted protected-path validator')[0], 'Codex checkout must not leave credentials for the model'
assert 'gh auth setup-git' in impl.split('name: Open a PR instead of merging')[1], 'Push step must configure auth only after model+validator'
assert "ENABLE_CODEX_IMPLEMENT == 'true'" in impl, 'Codex implementation must be opt-in'
assert "'scripts/'" in (ROOT/'scripts/validate_agent_changes.py').read_text(), 'Entire trusted scripts/ path must be protected'
issue=(W/'claude-issues.yml').read_text()
assert 'contents: write' not in issue and 'pull-requests: write' not in issue, 'Claude issue job must be read-only until redesign'
for f in ['claude-review.yml','codex-review.yml','claude-issues.yml','codex-implement.yml']:
    wf=(W/f).read_text()
    assert 'scripts/require_pinned_model_action.py' in wf, f'Fail-closed pin preflight missing: {f}'

for f in W.glob('*.yml'):
    d=yaml.safe_load(f.read_text()); assert isinstance(d,dict) and d.get('jobs'), f
print('PASS security policy: no model secrets in PR CI, review manual/trusted-base, implement validator staged, generated tests deferred to CI')
