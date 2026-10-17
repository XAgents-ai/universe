#!/usr/bin/env python3
"""Offline audit that the exported collaboration package retains critical files and no journal."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
required = [
    'UNIVERSE_V0_PHYSICS_SPEC.md', 'v0_kernel.py', 'v0_oracle.py',
    'v0_responder.py', 'open_world.py', 'server.py', 'run_checks.sh',
    '.github/workflows/ci.yml', '.github/workflows/claude-review.yml',
    '.github/workflows/codex-review.yml', '.github/workflows/codex-implement.yml',
    'docs/SCIENTIFIC_CLAIMS.md', 'docs/GITHUB_SETUP.md', 'AGENTS.md', 'CLAUDE.md'
]
for name in required:
    assert (root/name).is_file(), f'Missing required file: {name}'
assert not (root/'.universe_state').exists(), 'Private session journal was included!'
print('PASS: essential source and collaboration workflows included; no runtime journal')
