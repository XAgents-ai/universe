#!/usr/bin/env python3
"""Fail closed before a credentialed model action if its workflow uses a mutable ref.

Usage: python scripts/require_pinned_model_action.py <workflow-yml> <owner/name>
The repository owner must independently verify the SHA resolves to the intended upstream commit.
"""
import re, sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit('usage: require_pinned_model_action.py workflow.yml owner/repo')
workflow, action = sys.argv[1:]
path = Path(workflow)
if path.parent.name != 'workflows' or path.parent.parent.name != '.github':
    raise SystemExit('refusing unexpected workflow path')
text = path.read_text()
refs = re.findall(r'(?m)^\s*-\s*uses:\s*' + re.escape(action) + r'@([^\s#]+)', text)
if len(refs) != 1 or not re.fullmatch(r'[0-9a-f]{40}', refs[0]):
    raise SystemExit(f'BLOCKED: {action} in {path} must use one verified 40-hex immutable commit SHA, got {refs!r}')
print(f'PASS: pinned model action: {action}@{refs[0]}')
