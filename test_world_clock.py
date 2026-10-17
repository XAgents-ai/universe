"""W1 - world-owned clock: acceptance tests W1-01..W1-06 (docs/issues/01-world-clock.md).

Principle under test: time belongs to the universe, not to whoever makes the most API requests.
Every test runs LiveUniverse in manual clock mode (tick_seconds=0) except W1-04, which runs the scheduler.
"""
from __future__ import annotations
import itertools, json, tempfile, time
from pathlib import Path
from unittest.mock import patch
from open_world import LiveUniverse, ClockPolicy, build_shared_world, canonical_batch, JOURNAL_FORMAT
from v0_kernel import World, Params

MANUAL=lambda: ClockPolicy(tick_seconds=0)


def contested_world():
    """Two participants' seed sites draw from ONE shared store holding a single quantum: a genuine
    physical conflict whose winner must be decided by the pre-registered rule, never by arrival order."""
    w=World(12,8,WORLD_SEED:=99,Params())
    w.place((5,3),'B',q=1)                      # the only usable energy for both sites
    w.place((4,3),'K','S');w.place((6,3),'K','S')
    w.place((4,4),'C','S');w.place((6,4),'C','S');w.place((4,5),'A','S');w.place((6,5),'A','S')
    w.bond_path([(4,3),(4,4),(4,5)]);w.bond_path([(6,3),(6,4),(6,5)]);w.bond((4,3),(5,3));w.bond((5,3),(6,3))
    w.run({},3)
    return w


class Contested(LiveUniverse):
    """Shared-world layout where entrant-0 owns K(4,3) and entrant-1 owns K(6,3) (SITE_X overridden)."""
    def __init__(self,root,clock=None):
        super().__init__(root,clock=clock,world_factory=contested_world)
    def join(self,controller='human',global_exposure_declared=False):
        import open_world
        saved=(open_world.SITE_X,open_world.SITE_Y)
        open_world.SITE_X,open_world.SITE_Y=(4,6),3
        try:return super().join(controller,global_exposure_declared)
        finally:open_world.SITE_X,open_world.SITE_Y=saved


def w1_01_permutation_invariance():
    """Permuting submission arrival order produces the same state hash (same seed, same accepted batch)."""
    actions=[('human','set'),('model','observe'),('program','set')]
    hashes=set();batches=set()
    for order in itertools.permutations(range(3)):
        with tempfile.TemporaryDirectory() as d:
            u=LiveUniverse(d,clock=MANUAL())
            toks=[u.join(c)['token'] for c,_ in actions]
            sites=[u.actor_view(t)['authorized'][0] for t in toks]
            for i in order:                                     # arrival order varies
                u.submit(toks[i],actions[i][1],*sites[i])
            rec=u.advance()
            hashes.add(u.w.state_hash());batches.add(json.dumps(rec['batch']))
    assert len(hashes)==1 and len(batches)==1,(hashes,batches)
    # contested resource: one quantum, two claimants, every arrival order -> one identical outcome
    results=set()
    for order in [(0,1),(1,0)]:
        with tempfile.TemporaryDirectory() as d:
            u=Contested(d,clock=MANUAL())
            toks=[u.join('human')['token'],u.join('model')['token']]
            for i in order:u.submit(toks[i],'set',*u.actor_view(toks[i])['authorized'][0])
            rec=u.advance()
            results.add((u.w.state_hash(),json.dumps(rec['outcomes'])))
    assert len(results)==1,results
    outcomes=json.loads(next(iter(results))[1])
    winners=[o['agent'] for o in outcomes if o['result']=='ok'];losers=[o['agent'] for o in outcomes if o['result']=='refused:no-energy']
    assert len(winners)==1 and len(losers)==1,outcomes
    # and the pre-registered rule rotates priority with the tick, so standing priority does not exist
    order_t3=[a for a,_ in canonical_batch({'entrant-0':1,'entrant-1':1},3)]
    order_t4=[a for a,_ in canonical_batch({'entrant-0':1,'entrant-1':1},4)]
    assert order_t3!=order_t4
    print('PASS W1-01 permuting arrival order yields one state hash and one batch; contested quantum resolved by the registered rule, not arrival')


def w1_02_polling_is_free_and_inert():
    """Repeated polling or observing does not advance the world or yield unpaid observations."""
    with tempfile.TemporaryDirectory() as d:
        u=LiveUniverse(d,clock=MANUAL());t=u.join('human')['token'];site=u.actor_view(t)['authorized'][0]
        tick=u.w.tick;h=u.w.state_hash()
        for _ in range(200):u.actor_view(t);u.observer_view();u.clock_view()
        assert u.w.tick==tick and u.w.state_hash()==h
        store=u.w.store_of(tuple(site));q0=store.q
        v=u.submit(t,'observe',*site)
        assert v['submission']=='accepted' and v['observed']==[] and u.w.tick==tick,'submit must not execute or advance'
        for _ in range(50):assert u.actor_view(t)['observed']==[]
        u.advance()
        assert len(u.actor_view(t)['observed'])==1 and u.w.tick==tick+1
        assert u.w.store_of(tuple(site)).q==q0-1,'exactly one paid observation'
        for _ in range(50):assert len(u.actor_view(t)['observed'])==1 and u.w.tick==tick+1
        print('PASS W1-02 200 polls advance nothing; one submitted observe = one charged observation delivered after the tick')


def w1_03_duplicate_submission_single_effect():
    """A participant cannot produce two effects in one tick; the second submission is refused."""
    with tempfile.TemporaryDirectory() as d:
        u=LiveUniverse(d,clock=MANUAL());t=u.join('human')['token'];site=u.actor_view(t)['authorized'][0]
        q0=u.w.store_of(tuple(site)).q
        first=u.submit(t,'set',*site);second=u.submit(t,'set',*site);third=u.submit(t,'observe',*site)
        assert first['submission']=='accepted' and second['submission']=='refused:already-submitted' and third['submission']=='refused:already-submitted'
        rec=u.advance()
        mine=[b for b in rec['batch'] if b['agent']=='entrant-0']
        assert len(mine)==1 and mine[0]['op']=='set'
        assert len([e for e in u.w.log[-1]['agent']])==1
        drawn=q0-u.w.store_of(tuple(site)).q
        assert drawn==2,f'one set = write cost + one emitted quantum, got {drawn}'   # one effect, not two
        print('PASS W1-03 duplicate submission refused; exactly one action and one charge per participant per tick')


def w1_04_silent_participants_do_not_stop_time():
    """The world advances on its own clock policy while participants are silent; all-submitted ticks early."""
    with tempfile.TemporaryDirectory() as d:
        u=LiveUniverse(d,clock=ClockPolicy(tick_seconds=0.05,early_tick_when_all_submitted=False))
        try:
            u.join('human');tick=u.w.tick
            time.sleep(0.6)
            advanced=u.w.tick-tick
            assert advanced>=5,advanced
            events=u.observer_log()['events']
            assert all(e['batch']==[] for e in events if e['kind']=='tick')
        finally:u.close()
    with tempfile.TemporaryDirectory() as d:
        u=LiveUniverse(d,clock=ClockPolicy(tick_seconds=5.0,early_tick_when_all_submitted=True))
        try:
            toks=[u.join('human')['token'],u.join('model')['token']];tick=u.w.tick
            t0=time.monotonic()
            for t in toks:u.submit(t,'wait')
            while u.w.tick==tick and time.monotonic()-t0<2:time.sleep(0.01)
            assert u.w.tick==tick+1 and time.monotonic()-t0<2,'all-submitted should tick long before the 5 s interval'
        finally:u.close()
    print('PASS W1-04 silent participants cannot hold physics; scheduler ticks on its own and early when everyone has submitted')


def w1_05_restart_replays_batches_ledgers_hashes():
    """Restart and replay reproduce the same action batches, ledgers and state hashes."""
    with tempfile.TemporaryDirectory() as d:
        u=LiveUniverse(d,clock=MANUAL())
        toks=[u.join(c)['token'] for c in ('human','model','program')]
        sites=[u.actor_view(t)['authorized'][0] for t in toks]
        script=[[(0,'set'),(1,'observe')],[],[(2,'set'),(0,'wait'),(1,'set')],[(1,'observe')],[(0,'set'),(2,'set'),(1,'claim')]]
        for tick_actions in script:
            for i,k in tick_actions:u.submit(toks[i],k,*sites[i])
            u.advance()
        before=dict(hash=u.w.state_hash(),tick=u.w.tick,energy=u.w.energy(),
                    actors={t:(u.actor_view(t)['actions'],u.actor_view(t)['observed']) for t in toks})
        journal=[json.loads(l) for l in (Path(d)/'events.jsonl').read_text().splitlines()]
        assert all(r['format']==JOURNAL_FORMAT for r in journal)
        assert sum(r['kind']=='tick' for r in journal)==len(script)
        v=LiveUniverse(d,clock=MANUAL())
        assert v.w.state_hash()==before['hash'] and v.w.tick==before['tick'] and v.w.energy()==before['energy']
        for t in toks:assert (v.actor_view(t)['actions'],v.actor_view(t)['observed'])==before['actors'][t]
        assert v.pending=={} ,'pending submissions are not world transitions and are not replayed'
        # ledger recorded in each tick record equals the replayed ledger at that tick
        w=build_shared_world();w.run({},0)
        for r in journal:
            if r['kind']=='join':w.grant(r['agent'],tuple(r['site']))
            else:
                ev=w.step(agent_ops=[(b['agent'],b['op'],tuple(b['pos'])) for b in r['batch'] if b['op']!='wait'])
                assert ev['energy']==r['energy'] and w.state_hash()==r['world_hash']
        print('PASS W1-05 restart replays every batch; ledgers and state hashes match the journal tick for tick')


def w1_06_failed_commit_leaves_published_world_unchanged():
    """A failed journal commit leaves the published world, actors and pending queue unchanged; further ticks refused."""
    with tempfile.TemporaryDirectory() as d:
        u=LiveUniverse(d,clock=MANUAL());t=u.join('human')['token'];site=u.actor_view(t)['authorized'][0]
        u.submit(t,'set',*site)
        h=u.w.state_hash();tick=u.w.tick;actions=u.actor_view(t)['actions'];pend=dict(u.pending)
        good=(Path(d)/'events.jsonl').read_bytes()
        with patch('open_world.os.fsync',side_effect=OSError('disk failed')):
            try:u.advance()
            except OSError:pass
            else:raise AssertionError('journal failure did not propagate')
        assert u.w.state_hash()==h and u.w.tick==tick and u.actor_view(t)['actions']==actions and u.pending==pend
        assert u._poisoned and u.clock_view()['journal_poisoned']
        try:u.advance()
        except RuntimeError as e:assert 'restart' in str(e)
        else:raise AssertionError('poisoned journal allowed another tick')
        # the durable history is either the pre-failure prefix or that prefix plus one complete record: never ahead of memory by more
        assert (Path(d)/'events.jsonl').read_bytes()[:len(good)]==good
        v=LiveUniverse(d,clock=MANUAL())
        assert v.w.tick in (tick,tick+1)
        print('PASS W1-06 failed journal commit leaves the published world unchanged and blocks further ticks until restart')


if __name__=='__main__':
    for f in [w1_01_permutation_invariance,w1_02_polling_is_free_and_inert,w1_03_duplicate_submission_single_effect,
              w1_04_silent_participants_do_not_stop_time,w1_05_restart_replays_batches_ledgers_hashes,
              w1_06_failed_commit_leaves_published_world_unchanged]:f()
