"""T2/R2/R3: journal confidentiality, atomic state commits, strict replay."""
from __future__ import annotations
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from open_world import LiveUniverse


def test_token_not_persisted():
    with tempfile.TemporaryDirectory() as folder:
        u=LiveUniverse(folder)
        a=u.join('human');token=a['token']
        u.act(token,'observe',3,4)
        data=(Path(folder)/'events.jsonl').read_text()
        assert token not in data
        assert 'token_hash' in data and '\"token\"' not in data
        assert token not in json.dumps(u.observer_log())
        v=LiveUniverse(folder)
        assert v.actor_view(token)['observed']
        print('PASS T2 token not in persisted journal or observer export; reload authorized by digest')


def test_step_commit_failure_is_atomic():
    with tempfile.TemporaryDirectory() as folder:
        u=LiveUniverse(folder);token=u.join()['token']
        start=u.w.state_hash();n=u.actor_view(token)['calls']
        with patch.object(u,'_commit',side_effect=OSError('injected failure')):
            try:u.act(token,'set',3,4)
            except OSError:pass
            else:raise AssertionError('injected journal error did not propagate')
        assert u.w.state_hash()==start and u.actor_view(token)['calls']==n
        assert LiveUniverse(folder).w.state_hash()==start
        print('PASS R3 failed step commit leaves memory and durable journal at same state')


def test_join_commit_failure_is_atomic():
    with tempfile.TemporaryDirectory() as folder:
        u=LiveUniverse(folder);start=u.w.state_hash()
        with patch.object(u,'_commit',side_effect=OSError('injected failure')):
            try:u.join()
            except OSError:pass
            else:raise AssertionError('injected join error did not propagate')
        assert u.next_slot==0 and not u.by_token and u.w.state_hash()==start
        print('PASS R3 failed join does not consume an entry site')


def test_torn_tail_recovered_complete_records_preserved():
    with tempfile.TemporaryDirectory() as folder:
        u=LiveUniverse(folder);token=u.join()['token'];u.act(token,'set',3,4)
        good=(Path(folder)/'events.jsonl').read_bytes();expected=u.w.state_hash()
        assert good.endswith(b'\n')
        with open(Path(folder)/'events.jsonl','ab') as f:f.write(b'{"kind":"step","token_hash":"partial')
        replay=LiveUniverse(folder)
        assert replay.w.state_hash()==expected
        assert (Path(folder)/'events.jsonl').read_bytes()==good
        replay.act(token,'wait')
        assert LiveUniverse(folder).w.state_hash()==replay.w.state_hash()
        print('PASS R2 unterminated trailing fragment discarded; committed history replays')


def test_completed_tamper_is_rejected():
    with tempfile.TemporaryDirectory() as folder:
        u=LiveUniverse(folder);u.join()
        p=Path(folder)/'events.jsonl'
        lines=p.read_text().splitlines();r=json.loads(lines[0]);r['controller']='fake'
        p.write_text(json.dumps(r)+'\n')
        try:LiveUniverse(folder)
        except RuntimeError as e:assert 'Altered journal' in str(e)
        else:raise AssertionError('complete altered event was silently accepted')
        print('PASS R2 complete forged journal event rejected')


def test_disk_commit_failure_poisoned():
    with tempfile.TemporaryDirectory() as folder:
        u=LiveUniverse(folder);token=u.join()['token'];start=u.w.state_hash()
        with patch('open_world.os.fsync',side_effect=OSError('disk failed')):
            try:u.act(token,'set',3,4)
            except OSError:pass
            else:raise AssertionError('disk write error did not propagate')
        assert u.w.state_hash()==start and u._poisoned
        try:u.act(token,'wait')
        except RuntimeError as e:assert 'restart' in str(e)
        else:raise AssertionError('poisoned journal allowed another step')
        print('PASS R3 journal write failure blocks further mutations until restart')


if __name__=='__main__':
    for f in [test_token_not_persisted,test_step_commit_failure_is_atomic,test_join_commit_failure_is_atomic,
              test_torn_tail_recovered_complete_records_preserved,test_completed_tamper_is_rejected,
              test_disk_commit_failure_poisoned]:f()
