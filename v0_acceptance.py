"""
Universe V0 - executable acceptance checks for the milestone, on rule set R0.

What this file demonstrates (honestly scoped):
  I2  bounded agent authority: the only agent primitive is a charged control-site write
  I3  autonomous continuation + exact replay
  I4  environmental response with a causal-path intervention (cut the sensor->controller wire)
  I5  per-tick energy and matter ledger, incl. a fuzz over random worlds
  +   agent-driven assembly of a bonded structure through control sites (push, then weld)

What it does NOT demonstrate:
  I1  a legal construction trajectory for the responder machine from raw matter.
      The machine below is hand-placed (oracle obligation 1 only). Obligation 2 is the
      ConstructionOracle's job and is unimplemented here.
"""
import random
from v0_kernel import World, Params, SPECIES, ORDER

AG = 'agent-0'


def build_milestone_world(seed=7):
    w = World(14, 12, seed, Params())
    # --- responder machine M: sensor -> wire -> gate(with inhibit) -> wire -> mover
    w.add_source((6, 3), 'S', 2); w.place((6, 4), 'B')           # world-owned sun feeding P's store
    w.place((6, 5), 'P', 'E')                                     # senses (7,5); emits to (5,5)
    w.place((5, 5), 'C', 'W')                                     # -> G at (4,5), arrives on G's left
    w.place((4, 5), 'G', 'S')                                     # inhibit from (4,4), output to (4,6)
    w.place((4, 6), 'C', 'S'); w.place((4, 7), 'A', 'S')          # mover pushes (4,8) -> (4,9)
    w.place((4, 8), 'S')                                          # the object to be moved
    # --- inhibit line, controllable by the agent while connected
    w.add_source((3, 2), 'S', 2); w.place((3, 3), 'B')
    w.place((4, 3), 'K', 'S'); w.place((4, 4), 'C', 'S')
    # --- entry actuator for assembly: K -> C -> A pushes S(9,5) to (9,6); K -> C -> W welds (9,6)-(9,7)
    w.add_source((11, 2), 'W', 2); w.place((10, 2), 'B')
    w.place((9, 2), 'K', 'S'); w.place((9, 3), 'C', 'S'); w.place((9, 4), 'A', 'S')
    w.place((9, 5), 'S'); w.place((9, 7), 'S')
    w.add_source((11, 6), 'S', 2); w.place((11, 7), 'B')
    w.place((11, 8), 'K', 'W'); w.place((10, 8), 'C', 'W'); w.place((9, 8), 'W', 'N')
    for k in [(4, 3), (9, 2), (11, 8)]: w.grant(AG, k)
    # weld the machine and the entry actuators (the object at (4,8) and raw S at (9,5),(9,7) stay free)
    w.bond_path([(6, 4), (6, 5), (5, 5), (4, 5), (4, 6), (4, 7)]); w.bond_path([(4, 5), (4, 4), (4, 3), (3, 3)])
    w.bond_path([(10, 2), (9, 2), (9, 3), (9, 4)]); w.bond_path([(11, 7), (11, 8), (10, 8), (9, 8)])
    return w


def schedule_connected():
    return {
        20: ([(AG, 'set', (9, 2))], ()),                # push S(9,5) -> (9,6)
        25: ([(AG, 'set', (11, 8))], ()),               # weld (9,6)-(9,7)
        # Timing rule: a K written in phase 3 emits in phase 4 of the SAME tick.
        # K(4,3) set at t -> C(4,4) excited at t -> inhibit reaches G at t+1.
        # drop at t -> P emits at t -> C(5,5) excited at t -> signal reaches G at t+1.
        31: ([(AG, 'set', (4, 3))], [('drop', (7, 5), 'S', 'N')]),   # inhibit and signal meet at G on tick 32
        35: ((), [('remove', (7, 5))]),
        38: ([(AG, 'set', (9, 9))], ()),                # unauthorized / non-K write -> must be refused
    }


def check(cond, msg):
    print(('PASS ' if cond else 'FAIL ') + msg)
    return cond


def main():
    ok = True
    T_DISC = 40
    w = build_milestone_world()
    sched = schedule_connected()
    hashes_a = w.run(sched, T_DISC)

    # assembly through control sites
    acts = [a for ev in w.log for a in ev['acts']]
    ok &= check(('push', (9, 5), (9, 6)) in acts, "assembly: agent-triggered mover pushed S (9,5)->(9,6)")
    ok &= check(frozenset({(9, 6), (9, 7)}) in w.bonds, "assembly: agent-triggered welder bonded (9,6)-(9,7)")
    # inhibit demonstrates agent control over the machine while connected
    ok &= check(('push', (4, 8), (4, 9)) not in acts and (4, 8) in w.grid,
                "control: inhibited sensor event produced no push (gate inhibit path works)")
    # I2 bounded authority
    refused = [a for ev in w.log for a in ev['agent'] if a[3].startswith('refused')]
    ok &= check(len(refused) == 1 and refused[0][2] == (9, 9), "I2: write to a non-authorized site refused")
    ops = {a[1] for ev in w.log for a in ev['agent']}
    ok &= check(ops <= {'set', 'observe'}, "I2: agent primitives are only set/observe on control sites")

    # --- disconnect: no agent input from here on. Snapshot and clone counterfactuals.
    snap = w.clone(); snap.run({}, 45)
    cf = {name: snap.clone() for name in ('respond', 'cut', 'wrong-cell', 'quiet')}
    cf['respond'].run({46: ((), [('drop', (7, 5), 'S', 'N')])}, 60)
    cf['cut'].run({45: ((), [('replace', (4, 6), 'S', 'N')]), 46: ((), [('drop', (7, 5), 'S', 'N')])}, 60)
    cf['wrong-cell'].run({46: ((), [('drop', (8, 5), 'S', 'N')])}, 60)
    cf['quiet'].run({}, 60)

    def pushed(world): return any(a == ('push', (4, 8), (4, 9)) for ev in world.log[45:] for a in ev['acts'])
    ok &= check(pushed(cf['respond']), "I3/I4: after disconnect, sensor event -> object moved, no agent input consumed")
    ok &= check(not pushed(cf['cut']), "I4: same event with sensor->controller wire cut -> no movement (causal path)")
    ok &= check(not pushed(cf['wrong-cell']), "I4: event at a non-sensed cell -> no movement")
    ok &= check(not pushed(cf['quiet']), "I4: no event -> no movement")
    agent_consumed = sum(len(ev['agent']) for ev in cf['respond'].log[T_DISC:])
    ok &= check(agent_consumed == 0, "I3: zero agent operations consumed after disconnect")

    # I3 exact replay from scratch with the same seed and logged inputs
    w2 = build_milestone_world()
    full = dict(sched); full[46] = ((), [('drop', (7, 5), 'S', 'N')])
    hashes_b = w2.run(full, 60)
    hashes_ref = hashes_a + [ev['hash'] for ev in cf['respond'].log[T_DISC:]]
    ok &= check(hashes_b == hashes_ref, f"I3: replay reproduces all {len(hashes_b)} state hashes exactly")

    # I5 ledger was asserted every tick in every run above; now fuzz random worlds
    viol = 0; ticks = 0
    for s in range(40):
        rng = random.Random(1000 + s)
        fw = World(10, 10, 1000 + s, Params())
        for _ in range(28):
            p = (rng.randrange(10), rng.randrange(10))
            if fw.free_cell(p):
                sp = rng.choice(SPECIES)
                fw.place(p, sp, rng.choice(ORDER), q=rng.randrange(fw.P.Q_MAX + 1) if sp == 'B' else 0)
        for _ in range(4):
            p = (rng.randrange(10), rng.randrange(10))
            if fw.free_cell(p): fw.add_source(p, rng.choice(ORDER), rng.choice([1, 2, 3]))
        for p, pt in list(fw.grid.items()):
            if pt.sp == 'K': fw.grant(AG, p)
        ks = [p for p, pt in fw.grid.items() if pt.sp == 'K']
        try:
            for t in range(300):
                a = [(AG, rng.choice(['set', 'observe']), rng.choice(ks))] if ks and rng.random() < 0.3 else []
                e = [('drop', (rng.randrange(10), rng.randrange(10)), rng.choice(SPECIES), rng.choice(ORDER))] if rng.random() < 0.05 else []
                fw.step(a, e); ticks += 1
        except AssertionError as ex:
            viol += 1; print('   ', ex)
    ok &= check(viol == 0, f"I5: energy+matter ledger held on every one of {ticks} fuzzed ticks across 40 random worlds")

    e = cf['respond'].energy()
    print(f"\nledger at end of 'respond' run: {e}")
    print("\nNOT DEMONSTRATED BY THIS HAND-PLACED O1 TEST: I1 for the gated responder. See v0_responder.py for seeded P-A construction. "
          "Machine M was hand-placed; no O2 witness for this full gated design. A separate P-A responder O2 is implemented in v0_responder.py.")
    print("\nOVERALL:", "PASS" if ok else "FAIL")
    return ok


if __name__ == '__main__':
    main()
