#!/usr/bin/env python3
"""Trusted-base preflight, run from a copy made BEFORE any model can edit source.
Reject agent modifications to governance, credentials, workflows and evidence runner.
Not a substitute for a human reviewing the PR and branch protection.
"""
from pathlib import PurePosixPath
import subprocess,sys

def git(*args):
    return subprocess.check_output(['git',*args],text=True).splitlines()

changed=set(git('diff','--name-only'))
changed.update(git('diff','--name-only','--cached'))
changed.update(git('ls-files','--others','--exclude-standard'))
try: changed.update(git('diff','--name-only','main...HEAD'))
except subprocess.CalledProcessError: pass
forbidden_prefixes=('.github/','.universe_state/','.venv/','.env','node_modules/','secrets/','docs/issues/','docs/evidence/','scripts/')
forbidden_names={'AGENTS.md','CLAUDE.md','SECURITY.md','.gitignore',
 'run_checks.sh','scripts/validate_agent_changes.py','scripts/build_codex_task.py',
 'scripts/bootstrap_github.sh','scripts/bootstrap_github.ps1','scripts/seed_issues.sh',
 'docs/SCIENTIFIC_CLAIMS.md','docs/GITHUB_SETUP.md','docs/COLLABORATION.md',
 'scripts/test_workflow_boundaries.py','scripts/fetch_review_context.sh','scripts/audit_repository.py',
 'requirements.txt','requirements-dev.txt','verify_journal.py',
 'v0_kernel_r0.py','v0_kernel_r01.py','v0_kernel_r02.py'}
forbidden_suffixes={'.pem','.p12','.key','.pfx'}
errors=[]
for raw in sorted(changed):
    p=PurePosixPath(raw)
    if ('..' in p.parts or raw.startswith('/') or raw.startswith(forbidden_prefixes)
            or raw in forbidden_names or p.suffix.lower() in forbidden_suffixes):
        errors.append(raw)
if errors:
    print('REJECTED protected paths:',', '.join(errors),file=sys.stderr);sys.exit(1)
print('Permitted candidate paths:',len(changed))
