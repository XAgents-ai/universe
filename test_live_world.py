"""Regression tests for persistent shared world, actor/observer segregation and F6 (W1: submit + world clock)."""
from __future__ import annotations
import os, tempfile
os.environ.setdefault('UNIVERSE_TICK_SECONDS','0')   # manual clock for the in-process app under test
from pathlib import Path
from fastapi.testclient import TestClient
from open_world import LiveUniverse, ClockPolicy
from server import app, LIVE
from v0_kernel import World,Params


def test_shared_persistent_world():
    with tempfile.TemporaryDirectory() as folder:
        u=LiveUniverse(folder,clock=ClockPolicy(tick_seconds=0))
        alice=u.join('human');bob=u.join('model')
        a=alice['token'];b=bob['token']
        assert alice['agent']!=bob['agent']
        assert u.actor_view(a)['observed']==[] and u.actor_view(b)['observed']==[]
        assert not {'particles','energy','hash','sources','heat','frame'} & u.actor_view(a).keys()
        assert u.observer_view()['participant_count']==2
        # One actor moves matter; the OTHER actor inhabits the exact same evolving world.
        # W1: submissions never advance physics; the world's clock does. Two batched ticks below.
        u.submit(a,'set',3,4);u.submit(b,'observe',8,4);assert u.w.tick==20
        u.advance();u.submit(b,'wait');u.advance();u.advance()
        assert u.observer_view()['frame']['tick']==23
        assert any(p['x']==3 and p['y']==8 and p['species']=='S' for p in u.observer_view()['frame']['particles'])
        assert u.w.authorized('entrant-0',(3,4)) and not u.w.authorized('entrant-1',(3,4))
        u.submit(b,'set',3,4);u.advance();refused=u.actor_view(b)
        assert refused['actions'][-1]['result'].startswith('refused')
        assert u.w.log[-1]['agent'][0][3].startswith('refused')
        # No bypass for environmental intervention.
        try:u.submit(a,'drop',1,1)
        except ValueError:pass
        else:raise AssertionError('live participant gained boundary authority')
        before_hash=u.w.state_hash();before_tick=u.w.tick
        reloaded=LiveUniverse(folder,clock=ClockPolicy(tick_seconds=0))
        assert reloaded.w.state_hash()==before_hash and reloaded.w.tick==before_tick
        assert reloaded.actor_view(a)['actions']==u.actor_view(a)['actions']
        assert reloaded.actor_view(b)['observed']==u.actor_view(b)['observed']
        print('PASS shared actors inhabit same physical state, segregated observations, independent authorization, reload exact hashes')


def test_api():
    c=TestClient(app)
    a=c.post('/api/live/join',json={'controller':'human'}).json()
    b=c.post('/api/live/join',json={'controller':'model'}).json()
    assert 'token' in a and 'token' in b
    assert c.get('/api/live/actor').status_code==401
    actor=c.get('/api/live/actor',headers={'Authorization':'Bearer '+a['token']}).json()
    assert not {'frame','energy','sources','heat','bonds','particles','hash'} & actor.keys()
    forbidden=c.post('/api/live/act',headers={'Authorization':'Bearer '+a['token']},json={'kind':'drop','x':1,'y':1})
    assert forbidden.status_code==403
    r=c.post('/api/live/act',headers={'Authorization':'Bearer '+a['token']},json={'kind':'set','x':3,'y':4});r.raise_for_status()
    assert r.json()['submission']=='accepted' and c.get('/api/live/observer').json()['frame']['tick']==20,'HTTP submit must not advance physics'
    assert c.post('/api/live/act',headers={'Authorization':'Bearer '+a['token']},json={'kind':'set','x':3,'y':4}).json()['submission']=='refused:already-submitted'
    clock=c.get('/api/live/clock').json();assert clock['privileged_tick_endpoint'] is False and clock['pending_submissions']==1
    LIVE.advance()                                   # the world's clock, not a request, moves time
    snap=c.get('/api/live/observer').json()
    assert 'particles' in snap['frame'] and snap['frame']['tick']==21 and snap['clock']['pending_submissions']==0
    events=c.get('/api/live/events').json()['events']
    assert events and all('token' not in e for e in events)
    print('PASS live HTTP bearer auth, two participant types, read-only observer, no boundary writes, submit never advances physics')


if __name__=='__main__':
    test_shared_persistent_world()
    test_api()
