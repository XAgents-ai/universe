"""
Oracle obligation-1 witness (hand-found, executable): a 1-bit memory cell in rule set R0,
assembled from C (wire), K (powered emitter), G (gate), B (store). R0 has no memory primitive.

Mechanism: a quantum circulates in a wire ring that passes through K. Each pass, K absorbs the
quantum into its store and emits two: one back into the ring (refresh) and one to a reader line
(non-destructive read, paid for by world-owned energy). A G in the ring erases the bit when an
inhibit pulse meets the circulating quantum.

Demonstrates: write (inject a pulse), hold (circulation across many ticks), read (pulse train
accumulating in a reader store), erase (timed inhibit). Obligation 2 - a legal construction
trajectory from raw matter - is NOT demonstrated here.
"""
from v0_kernel import World, Params

AG = 'agent-0'


def build():
    w = World(10, 13, 3, Params())
    # ring: K(5,5)E -> (6,5)S -> (6,6)S -> (6,7)S -> (6,8)W -> (5,8)W -> G(4,8)N -> (4,7)N -> (4,6)N -> (4,5)E -> K
    w.place((5, 5), 'K', 'E')
    for pos, o in [((6, 5), 'S'), ((6, 6), 'S'), ((6, 7), 'S'), ((6, 8), 'W'), ((5, 8), 'W'),
                   ((4, 7), 'N'), ((4, 6), 'N'), ((4, 5), 'E')]:
        w.place(pos, 'C', o)
    w.place((4, 8), 'G', 'N')                                  # ring enters on G's right side; inhibit from (4,9)
    w.place((5, 6), 'B'); w.add_source((5, 7), 'N', 2)        # K's store, fed by a world-owned source inside the ring
    # reader: K's left output (5,4) -> (5,3) -> counter store (5,2)
    w.place((5, 4), 'C', 'N'); w.place((5, 3), 'C', 'N'); w.place((5, 2), 'B')
    # writer: K_w(8,6)W -> C(7,6)W -> ring cell (6,6)
    w.place((8, 6), 'K', 'W'); w.place((7, 6), 'C', 'W'); w.place((8, 5), 'B'); w.add_source((8, 4), 'S', 2)
    # eraser: K_e(4,10)N -> C(4,9)N -> G inhibit
    w.place((4, 10), 'K', 'N'); w.place((4, 9), 'C', 'N'); w.place((3, 10), 'B'); w.add_source((2, 10), 'E', 2)
    w.grant(AG, (8, 6)); w.grant(AG, (4, 10))
    # weld every structure: unbonded particles diffuse when their cell heats up
    w.bond_path([(5, 5), (6, 5), (6, 6), (6, 7), (6, 8), (5, 8), (4, 8), (4, 7), (4, 6), (4, 5), (5, 5)])
    w.bond_path([(5, 5), (5, 6)]); w.bond_path([(5, 5), (5, 4), (5, 3), (5, 2)])
    w.bond_path([(8, 6), (7, 6), (6, 6)]); w.bond_path([(8, 6), (8, 5)])
    w.bond_path([(4, 10), (4, 9), (4, 8)]); w.bond_path([(4, 10), (3, 10)])
    return w


def ring_quanta(w):
    ring = [(5, 5), (6, 5), (6, 6), (6, 7), (6, 8), (5, 8), (4, 8), (4, 7), (4, 6), (4, 5)]
    return sum(w.grid[p].x for p in ring if w.grid[p].sp in ('C', 'G')) + w.grid[(5, 5)].c


def main():
    w = build()
    w.run({}, 20)                                              # stores charge from sources
    assert ring_quanta(w) == 0 and w.grid[(5, 2)].q == 0
    # WRITE
    w.run({20: ([(AG, 'set', (8, 6))], ())}, 24)
    # HOLD + READ: run 80 ticks with no agent input
    w.run({}, 104)
    reads = w.grid[(5, 2)].q
    held = ring_quanta(w)
    print(f"write at t=20; at t=104 ring holds {held} quantum, reader store counted {reads} read pulses (cap {w.P.Q_MAX})")
    ok = held == 1 and reads >= 4
    # ERASE: the controller predicts (deterministically) when the quantum reaches (5,8) and times the inhibit.
    # The quantum at (5,8) at the start of tick t_s enters G during t_s. The inhibit must enter G the
    # same tick, so C(4,9) must already be excited: K_e is written at t_s - 1 (a K emits the tick it is set).
    probe = w.clone(); t_s = None
    for t in range(w.tick + 1, w.tick + 40):
        probe.step()
        if probe.grid[(5, 8)].x == 1: t_s = t; break
    assert t_s is not None
    w.run({}, t_s - 1)
    w.run({t_s - 1: ([(AG, 'set', (4, 10))], ())}, t_s + 30)
    print(f"erase: inhibit written at tick {t_s - 1} to meet the quantum at G on tick {t_s}; at t={w.tick} ring holds {ring_quanta(w)} quanta")
    ok = ok and ring_quanta(w) == 0
    # CONTROL: an inhibit at the wrong time does nothing (bit survives)
    w2 = build(); w2.run({20: ([(AG, 'set', (8, 6))], ())}, 60)
    w2.run({60: ([(AG, 'set', (4, 10))], ())}, 90) if w2.grid[(5, 8)].x == 0 else None
    print(f"control: mistimed inhibit -> ring holds {ring_quanta(w2)} quantum at t={w2.tick}")
    ok = ok and ring_quanta(w2) == 1
    print("ledger:", w.energy())
    print("MEMORY WITNESS:", "PASS" if ok else "FAIL")
    return ok


if __name__ == '__main__':
    main()
