"""W1 - world-owned clock: acceptance tests W1-01..W1-06 (docs/issues/01-world-clock.md).

Principle under test: time belongs to the universe, not to whoever makes the most API requests.
Every test runs LiveUniverse in manual clock mode (tick_seconds=0) except W1-04, which runs the scheduler.
"""
from __future__ import annotations
import itertools, json, tempfile, time
from pathlib import Path
from unittest.mock import patch
from collections import Counter
from open_world import LiveUniverse, ClockPolicy, build_shared_world, canonical_batch, JOURNAL_FORMAT, WORLD_SEED
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
    # Review finding C: a rotation rule gave the same actor first place on every even tick. The seeded
    # permutation must show no standing priority on sparse, periodic contests. 300 contests on even ticks
    # only, two and three contestants: each contestant leads within a binomial band around 1/n.
    for n,(lo,hi) in {2:(0.40,0.60),3:(0.23,0.44)}.items():
        pend={f'entrant-{i}':1 for i in range(n)}
        lead=Counter(canonical_batch(pend,t,WORLD_SEED)[0][0] for t in range(1000,1600,2))
        share={a:c/300 for a,c in lead.items()}
        assert len(lead)==n and all(lo<=v<=hi for v in share.values()),share
        odd=Counter(canonical_batch(pend,t,WORLD_SEED)[0][0] for t in range(1001,1601,2))
        assert len(odd)==n
    # ...and the order is a function of (seed, tick) only: identical across calls, different across seeds
    assert canonical_batch({'entrant-0':1,'entrant-1':1},20,WORLD_SEED)==canonical_batch({'entrant-0':1,'entrant-1':1},20,WORLD_SEED)
    assert any(canonical_batch({'entrant-0':1,'entrant-1':1},t,WORLD_SEED)!=canonical_batch({'entrant-0':1,'entrant-1':1},t,WORLD_SEED+1) for t in range(50))
    print('PASS W1-01 permuting arrival order yields one state hash and one batch; contested quantum resolved by the registered rule; no standing priority on sparse even-tick contests (2 and 3 contestants, 300 each)')


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
        u=LiveUniverse(d,clock=ClockPolicy(tick_seconds=0.05))
        try:
            u.join('human');tick=u.w.tick
            time.sleep(0.6)
            advanced=u.w.tick-tick
            assert 5<=advanced<=14,advanced
            events=u.observer_log()['events']
            assert all(e['batch']==[] for e in events if e['kind']=='tick')
        finally:u.close()
    # Review finding B: request volume must not shorten a tick. One participant (who is, alone, "everyone")
    # submits as fast as possible for 1.2 s under a 0.5 s interval: at most 3 ticks, never 40+.
    with tempfile.TemporaryDirectory() as d:
        u=LiveUniverse(d,clock=ClockPolicy(tick_seconds=0.5))
        try:
            t=u.join('human')['token'];tick=u.w.tick;n=0;end=time.monotonic()+1.2
            while time.monotonic()<end:u.submit(t,'wait');n+=1
            advanced=u.w.tick-tick
            assert 1<=advanced<=3,f'{n} submissions accelerated the clock to {advanced} ticks in 1.2 s'
            assert u.clock_view()['early_tick'] is False
        finally:u.close()
    print(f'PASS W1-04 silent participants cannot hold physics ({advanced} ticks from {n} rapid submissions in 1.2 s at 0.5 s/tick); no early tick, no acceleration')


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


def w1_07_poisoned_world_refuses_submissions():
    """Review finding A: after a journal failure the world must never acknowledge an action it cannot execute."""
    with tempfile.TemporaryDirectory() as d:
        u=LiveUniverse(d,clock=MANUAL());token=u.join()['token']
        with patch('open_world.os.fsync',side_effect=OSError('disk failed')):
            try:u.advance()
            except OSError:pass
            else:raise AssertionError('journal failure did not propagate')
        assert u._poisoned
        try:u.submit(token,'wait')
        except RuntimeError as e:assert 'not accepting' in str(e)
        else:raise AssertionError('poisoned world acknowledged a submission')
        assert u.pending=={} and u.actor_view(token)['submissions']==[]
    # and the HTTP mapping is a non-200 status, not a 200 with "accepted"
    import os
    os.environ['UNIVERSE_TICK_SECONDS']='0'
    from fastapi.testclient import TestClient
    import server
    c=TestClient(server.app)
    j=c.post('/api/live/join',json={'controller':'program'}).json();h={'Authorization':'Bearer '+j['token']}
    with patch('open_world.os.fsync',side_effect=OSError('disk failed')):
        try:server.LIVE.advance()
        except OSError:pass
    r=c.post('/api/live/act',json={'kind':'wait'},headers=h)
    assert r.status_code==503,(r.status_code,r.text)
    assert c.get('/api/live/clock').json()['journal_poisoned'] is True
    server.LIVE._poisoned=False   # restore the shared test instance for any later test in this process
    print('PASS W1-07 poisoned journal: submissions refused in-process and HTTP 503, never acknowledged')


def w1_08_single_writer_guard():
    """Deployment guard: one authoritative writer per state directory."""
    with tempfile.TemporaryDirectory() as d:
        a=LiveUniverse(d,clock=MANUAL(),single_writer=True)
        try:
            try:LiveUniverse(d,clock=MANUAL(),single_writer=True)
            except RuntimeError as e:assert 'another writer' in str(e)
            else:raise AssertionError('second writer started on the same journal')
        finally:a.close()
        b=LiveUniverse(d,clock=MANUAL(),single_writer=True);b.close()   # released on close
        print('PASS W1-08 a second authoritative writer on the same state directory refuses to start')


def w1_09_imports_without_fcntl():
    """Neo finding 1: the module must import and run on a platform without fcntl (Windows). Simulated by
    blocking the fcntl import in a subprocess; single_writer then needs msvcrt or fails with a clear message."""
    import subprocess, sys, textwrap
    code=textwrap.dedent('''
        import sys, tempfile; sys.modules['fcntl']=None
        import open_world
        from open_world import LiveUniverse, ClockPolicy
        d=tempfile.mkdtemp(); u=LiveUniverse(d,clock=ClockPolicy(tick_seconds=0)); t=u.join()['token']
        u.submit(t,'wait'); u.advance(); print('import-and-tick-ok', u.w.tick)
        try: LiveUniverse(tempfile.mkdtemp(),clock=ClockPolicy(tick_seconds=0),single_writer=True); print('guard-ok')
        except RuntimeError as e: print('guard-message:', 'no file-locking primitive' in str(e))
    ''')
    r=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True,timeout=120)
    assert r.returncode==0,r.stderr[-800:]
    assert 'import-and-tick-ok' in r.stdout and ('guard-ok' in r.stdout or 'guard-message: True' in r.stdout),r.stdout
    print('PASS W1-09 open_world imports and ticks without fcntl; the writer guard degrades with a clear message, not an ImportError')


def w1_10_clock_thread_errors_are_surfaced():
    """Neo finding 2: a failing tick must not be swallowed. The error is recorded, shown in clock_view(), and time resumes."""
    with tempfile.TemporaryDirectory() as d:
        u=LiveUniverse(d,clock=ClockPolicy(tick_seconds=0.05))
        try:
            u.join('human');real=u.advance;calls={'n':0}
            def flaky():
                calls['n']+=1
                if calls['n']==1:raise ValueError('injected kernel fault')
                return real()
            u.advance=flaky
            deadline=time.monotonic()+2
            while (u.clock_view()['tick_failures']==0 or u.w.tick<22) and time.monotonic()<deadline:time.sleep(0.02)
            cv=u.clock_view()
            assert cv['tick_failures']>=1 and cv['last_error'] is None or cv['last_error']['kind']=='ValueError',cv
            assert u.w.tick>=22,'clock did not resume after a failed tick'
        finally:u.close()
        print('PASS W1-10 a failing tick is counted and reported in clock_view; the clock keeps running')


if __name__=='__main__':
    for f in [w1_01_permutation_invariance,w1_02_polling_is_free_and_inert,w1_03_duplicate_submission_single_effect,
              w1_04_silent_participants_do_not_stop_time,w1_05_restart_replays_batches_ledgers_hashes,
              w1_06_failed_commit_leaves_published_world_unchanged,w1_07_poisoned_world_refuses_submissions,
              w1_08_single_writer_guard,w1_09_imports_without_fcntl,w1_10_clock_thread_errors_are_surfaced]:f()
