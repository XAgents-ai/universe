"""O2 for a minimal seeded autonomous physical responder: loose P + A -> bonded P-A.

The search finds physical assembly, not a 'create machine' primitive. The entry
actuators (three ordinary seed arms) are pre-placed initial conditions. The
sensor-to-actuator coupling is direct; a full P-C-G-C-A responder remains OPEN.
"""
from __future__ import annotations
import json
from pathlib import Path
from v0_kernel import World, Params
from v0_oracle import oracle_o2, replay

AG = 'agent-0'
BOND = frozenset(((5, 5), (6, 5)))
SITES = ((5, 1), (6, 10), (2, 5))


def seed_world(seed=7):
    w=World(15, 13, seed, Params())
    # construction arm #1: pushes A south
    w.add_source((3,1), 'E',2); w.place((4,1),'B'); w.place((5,1),'K','S'); w.place((5,2),'C','S'); w.place((5,3),'A','S')
    w.bond_path(((4,1),(5,1),(5,2),(5,3))); w.grant(AG,(5,1))
    # construction arm #2: pushes P north via two-step signal wire
    w.add_source((8,10),'W',2); w.place((7,10),'B'); w.place((6,10),'K','N'); w.place((6,9),'C','N'); w.place((6,8),'C','N'); w.place((6,7),'A','N')
    w.bond_path(((7,10),(6,10),(6,9),(6,8),(6,7))); w.grant(AG,(6,10))
    # construction arm #3: joins A and P, from perpendicular to the part paths
    w.add_source((1,4),'E',2); w.place((2,4),'B'); w.place((2,5),'K','E'); w.place((3,5),'C','E'); w.place((4,5),'W','E')
    w.bond_path(((2,4),(2,5),(3,5),(4,5))); w.grant(AG,(2,5))
    # World reservoir for the P sensor, independent from seed actuator fuel.
    w.add_source((7,4),'W',2); w.place((6,4),'B')
    # These are unbonded, free material inventory, not hand-placed functional machinery.
    w.place((5,4),'A','S'); w.place((6,6),'P','E'); w.place((5,6),'S')
    return w


def assembled(w):
    return (BOND in w.bonds and
        (5,5) in w.grid and w.grid[(5,5)].sp == 'A' and w.grid[(5,5)].o == 'S' and
        (6,5) in w.grid and w.grid[(6,5)].sp == 'P' and w.grid[(6,5)].o == 'E')


def construct(w, ops):
    """Use only controller writes and waits in the ordinary physics kernel."""
    schedule={int(t): ([(AG,op,tuple(pos))],()) for t,op,pos in ops if op}
    w.run(schedule, max(schedule or {w.tick:None})+4)
    return w


def response_trial(built, situation, horizon=10):
    w=built.clone()
    # Disconnect means no agent ops after construction, not an arbitrary physical edit.
    before=w.tick
    event={}
    if situation == 'cue': event[before]=((), [('drop',(7,5),'S','N')])
    if situation == 'wrong-cell': event[before]=((), [('drop',(8,5),'S','N')])
    if situation == 'path-cut':
        # Clone-only boundary intervention removes the P itself before stimulus.
        event[before]=((), [('remove',(6,5))])
        event[before+1]=((), [('drop',(7,5),'S','N')])
    w.run(event,before+horizon)
    changes=[a for e in w.log[before:] for a in e['acts']]
    moved=('push',(5,6),(5,7)) in changes
    disconnected=all(not e['agent'] for e in w.log[before:])
    return dict(moved=moved, disconnected=disconnected, effects=changes, energy=w.energy(), world=w)


def main():
    w=seed_world();w.run({},20)
    result=oracle_o2(w, list(SITES), assembled, max_depth=9, max_nodes=90_000)
    print('O2 autonomous responder:',{k:v for k,v in result.items() if k!='trace'},flush=True)
    assert result['status']=='WITNESS', result
    trace=result['trace']; print('CONTROL TRACE:',[(t,op) for t,op in trace if op],flush=True)
    direct=seed_world();direct.run({},20); replay(direct,trace,direct.tick+len(trace)+2)
    assert assembled(direct)
    assert all(a[1] in ('set','observe','claim') for e in direct.log[20:] for a in e['agent'])
    cue=response_trial(direct,'cue');quiet=response_trial(direct,'quiet');wrong=response_trial(direct,'wrong-cell');cut=response_trial(direct,'path-cut')
    assert cue['moved'] and cue['disconnected']
    assert not quiet['moved'] and not wrong['moved'] and not cut['moved']
    unbuilt=seed_world();unbuilt.run({},20)
    unbuilt_control=response_trial(unbuilt,'cue')
    assert not unbuilt_control['moved'],'unbuilt raw pieces responded as if already assembled'
    robust=0
    for seed in range(100,112):
        trial=seed_world(seed);trial.run({},20); replay(trial,trace,trial.tick+len(trace)+2)
        if assembled(trial) and response_trial(trial,'cue')['moved']:robust+=1
    assert robust==12,robust
    p=Path(__file__).with_name('o2_witness_autonomous_responder.json')
    p.write_text(json.dumps({'claim':'From pre-placed ordinary seed arms, assemble a physically coupled P-A responder from free matter; no hand-placement of P or A at final coordinates',
        'scope':'Direct P-to-A sensor coupling, not full P-C-G-C-A gate machine; no self-construction from raw matter',
        'seed':7,'warmup_ticks':20,'sites':[list(p) for p in SITES],
        'trace':[(t,op[0],list(op[1])) if op else (t,None,None) for t,op in trace],
        'search':{k:v for k,v in result.items() if k!='trace'},
        '12_seed_robust':robust, 'counterfactuals':{k:dict(moved=v['moved'],disconnected=v['disconnected']) for k,v in [('cue',cue),('quiet',quiet),('wrong-cell',wrong),('path-cut',cut),('unbuilt',unbuilt_control)]}},indent=2))
    print('PASS constructed bonded P-A; automatic response after disconnect; five causal comparisons including unbuilt; 12/12 fresh seeds',flush=True)
    return result


if __name__=='__main__':main()
