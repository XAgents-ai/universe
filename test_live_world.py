"""Regression tests for persistent shared world, actor/observer segregation and F6."""
from __future__ import annotations
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from open_world import LiveUniverse
from server import app
from v0_kernel import World,Params


def test_shared_persistent_world():
    with tempfile.TemporaryDirectory() as folder:
        u=LiveUniverse(folder)
        alice=u.join('human');bob=u.join('model')
        a=alice['token'];b=bob['token']
        assert alice['agent']!=bob['agent']
        assert u.actor_view(a)['observed']==[] and u.actor_view(b)['observed']==[]
        assert not {'particles','energy','hash','sources','heat','frame'} & u.actor_view(a).keys()
        assert u.observer_view()['participant_count']==2
        # One actor moves matter; the OTHER actor inhabits the exact same evolving world.
        aw=u.act(a,'set',3,4)
        u.act(b,'observe',8,4)
        u.act(b,'wait')
        assert u.observer_view()['frame']['tick']==23
        assert any(p['x']==3 and p['y']==8 and p['species']=='S' for p in u.observer_view()['frame']['particles'])
        assert u.w.authorized('entrant-0',(3,4)) and not u.w.authorized('entrant-1',(3,4))
        refused=u.act(b,'set',3,4)
        assert refused['actions'][-1]['result'].startswith('refused')
        assert u.w.log[-1]['agent'][0][3].startswith('refused')
        # No bypass for environmental intervention.
        try:u.act(a,'drop',1,1)
        except ValueError:pass
        else:raise AssertionError('live participant gained boundary authority')
        before_hash=u.w.state_hash();before_tick=u.w.tick
        reloaded=LiveUniverse(folder)
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
    c.post('/api/live/act',headers={'Authorization':'Bearer '+a['token']},json={'kind':'set','x':3,'y':4}).raise_for_status()
    snap=c.get('/api/live/observer').json()
    assert 'particles' in snap['frame'] and snap['frame']['tick']>=21
    events=c.get('/api/live/events').json()['events']
    assert events and all('token' not in e for e in events)
    print('PASS live HTTP bearer auth, two participant types, read-only observer, no boundary writes')


if __name__=='__main__':
    test_shared_persistent_world()
    test_api()
