#!/usr/bin/env python3
"""Exercise trusted protected-path checks in a clean disposable repository."""
from pathlib import Path
import subprocess, tempfile, shutil

src = Path(__file__).resolve().parent / 'validate_agent_changes.py'

def run(root, *args):
    return subprocess.run(args, cwd=root, capture_output=True, text=True)

with tempfile.TemporaryDirectory(prefix='universe-trusted-validator-') as td:
    root=Path(td)
    (root/'scripts').mkdir(); (root/'docs/issues').mkdir(parents=True)
    (root/'scripts/validate_agent_changes.py').write_bytes(src.read_bytes())
    (root/'docs/issues/acceptance.md').write_text('preapproved\n')
    (root/'v0_responder.py').write_text('print("baseline")\n')
    for args in [('git','init','-b','main'),('git','config','user.email','unit@example.invalid'),('git','config','user.name','Unit'),('git','add','.'),('git','commit','-m','baseline')]:
        r=run(root,*args)
        assert r.returncode==0, (args,r.stderr)
    cases=[
        ('docs/issues/acceptance.md',False),
        ('scripts/extra_helper.py',False),
        ('docs/evidence/results.txt',False),
        ('.github/workflows/new.yml',False),
        ('v0_responder.py',True),
    ]
    for name,allowed in cases:
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
        previous=path.read_bytes() if path.exists() else None
        path.write_text('changed\n')
        result=run(root,'python',str(root/'scripts/validate_agent_changes.py'))
        assert (result.returncode==0)==allowed, (name,result.stdout,result.stderr)
        if previous is None: path.unlink()
        else: path.write_bytes(previous)
        print('PASS' if not allowed else 'PASS', 'protected-path policy', name, 'allowed' if allowed else 'rejected')
