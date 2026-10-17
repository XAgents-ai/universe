"""
ConstructionOracle, obligation O2 (bounded reachability), plus the first seeded construction witness.

I1 is resolved as Claim 1 (per the review): from a pre-existing SEED actuator (an initial condition with a
verified material composition, obeying ordinary physics) an agent builds a second functioning element,
using only authorized, charged control-site writes.

Search model: breadth-first over ticks; one agent op per tick from {set K_i} U {wait}; canonical-conflict cold variant
(fluctuations off, transport and radiation on); visited set keyed by World.physical_key(). The result is
either a witness trace (shortest in ticks within the model) or NOT_ESTABLISHED with the bounds hit.
A found witness is then replayed under the REAL params across several seeds and its success rate reported.
"""
import json, sys, time
from collections import deque
from v0_kernel import World, Params

AG = 'agent-0'
TARGET = {(7, 4): ('C', 'S'), (7, 5): ('A', 'S')}
TARGET_BOND = frozenset({(7, 4), (7, 5)})


def build_seed_world(seed=11):
    """Seed actuator + loose parts. Every seed element is bonded; loose parts are free."""
    w = World(12, 10, seed, Params())
    # welder arm: source(5,1) -> B(6,1); K_w(7,1)S -> C(7,2)S -> W_t(7,3)S welds (7,4)-(7,5)
    w.add_source((5, 1), 'E', 2); w.place((6, 1), 'B')
    w.place((7, 1), 'K', 'S'); w.place((7, 2), 'C', 'S'); w.place((7, 3), 'W', 'S')
    w.bond_path([(6, 1), (7, 1), (7, 2), (7, 3)])
    # mover arm 1: K1(3,4)E -> C(4,4)E -> M1(5,4)E pushes (6,4)->(7,4); store on K1's right (3,5)
    w.add_source((3, 6), 'N', 2); w.place((3, 5), 'B')
    w.place((3, 4), 'K', 'E'); w.place((4, 4), 'C', 'E'); w.place((5, 4), 'A', 'E')
    w.bond_path([(3, 5), (3, 4), (4, 4), (5, 4)])
    # mover arm 2: K2(9,8)N -> C(9,7)N -> C(9,6)N -> M2(9,5)W pushes (8,5)->(7,5); store (10,8)
    w.add_source((11, 8), 'W', 2); w.place((10, 8), 'B')
    w.place((9, 8), 'K', 'N'); w.place((9, 7), 'C', 'N'); w.place((9, 6), 'C', 'N'); w.place((9, 5), 'A', 'W')
    w.bond_path([(10, 8), (9, 8), (9, 7), (9, 6), (9, 5)])
    # rotator arm: K_r(6,7)N -> C(6,6)N -> R(6,5)N rotates the part at (6,4); store behind K_r at (6,8)
    w.add_source((6, 9), 'N', 2); w.place((6, 8), 'B')
    w.place((6, 7), 'K', 'N'); w.place((6, 6), 'C', 'N'); w.place((6, 5), 'R', 'N')
    w.bond_path([(6, 8), (6, 7), (6, 6), (6, 5)])
    # signal arm (function test only): K_s(10,4)W -> C(9,4)W -> C(8,4)W -> (7,4); store (10,3)
    w.add_source((10, 2), 'S', 2); w.place((10, 3), 'B')
    w.place((10, 4), 'K', 'W'); w.place((9, 4), 'C', 'W'); w.place((8, 4), 'C', 'W')
    w.bond_path([(10, 3), (10, 4), (9, 4), (8, 4)])
    # loose parts: C' mis-oriented (E, must become S), A' correctly oriented, and the test object
    w.place((6, 4), 'C', 'E'); w.place((8, 5), 'A', 'S'); w.place((7, 6), 'S')
    for k in [(7, 1), (3, 4), (9, 8), (6, 7), (10, 4)]: w.grant(AG, k)
    return w


def goal(w):
    for pos, (sp, o) in TARGET.items():
        pt = w.grid.get(pos)
        if not pt or pt.sp != sp or pt.o != o: return False
    return TARGET_BOND in w.bonds


def distance(w):
    d = 0
    for pos, (sp, o) in TARGET.items():
        pt = w.grid.get(pos)
        if not pt or pt.sp != sp: d += 2
        elif pt.o != o: d += 1
    return d + (0 if TARGET_BOND in w.bonds else 1)


def oracle_o2(start, sites, goal_fn, max_depth=14, max_nodes=150_000):
    """BFS over agent op sequences; returns dict(status, trace|bounds, nodes, depth)."""
    cold = start.clone(); cold.P = cold.P.cold()
    ops = [None] + [('set', s) for s in sites]
    frontier = deque([(cold, [])])
    seen = {cold.physical_key()}
    nodes = 0; depth_reached = 0; t0 = time.time()
    while frontier:
        w, trace = frontier.popleft()
        if len(trace) > depth_reached: depth_reached = len(trace)
        if len(trace) >= max_depth: continue
        for op in ops:
            w2 = w.clone()
            w2.step(agent_ops=[(AG, op[0], op[1])] if op else ())
            nodes += 1
            key = w2.physical_key()
            if key in seen: continue
            seen.add(key)
            tr = trace + [(w.tick, op)]
            if goal_fn(w2):
                return dict(status='WITNESS', trace=tr, nodes=nodes, depth=len(tr), secs=round(time.time() - t0, 2),
                            exhausted_depth=None)
            frontier.append((w2, tr))
            if nodes >= max_nodes:
                return dict(status='NOT_ESTABLISHED', reason='node-cap', nodes=nodes, depth=depth_reached,
                            bounds=dict(max_depth=max_depth, max_nodes=max_nodes), secs=round(time.time() - t0, 2))
    return dict(status='NOT_ESTABLISHED', reason='exhausted', nodes=nodes, depth=depth_reached,
                bounds=dict(max_depth=max_depth, max_nodes=max_nodes), secs=round(time.time() - t0, 2))


def replay(world, trace, until):
    sched = {}
    for t, op in trace:
        if op: sched[t] = ([(AG, op[0], op[1])], ())
    world.run(sched, until)
    return world


def main():
    T_CHARGE = 20
    seed = build_seed_world()
    seed.run({}, T_CHARGE)
    sites = [s for s in seed.authorized_sites(AG) if s != (10, 4)]   # the signal arm is not a construction tool
    print(f"seed world charged to t={T_CHARGE}; construction sites {sites}; distance-to-goal {distance(seed)}")

    res = oracle_o2(seed, sites, goal)
    print("oracle O2:", {k: v for k, v in res.items() if k != 'trace'})
    if res['status'] != 'WITNESS':
        print("I1 (Claim 1): NOT ESTABLISHED within bounds"); return False
    trace = res['trace']
    print("witness trace:", [(t, op) for t, op in trace if op])
    json.dump(dict(trace=[(t, op[0] if op else None, op[1] if op else None) for t, op in trace],
                   target=[(k, v) for k, v in TARGET.items()], bond=sorted(TARGET_BOND), bounds=res.get('bounds'),
                   nodes=res['nodes'], seed=seed.seed), open('o2_witness_second_element.json', 'w'), indent=1)

    # 1. replay the witness under REAL params from the same initial state (same seed)
    real = build_seed_world(); real.run({}, T_CHARGE)
    replay(real, trace, T_CHARGE + res['depth'] + 2)
    ok = goal(real); print(f"replay under real params, same seed: goal reached = {ok}")

    # 2. robustness: the same trace under fresh seeds (thermal fluctuations differ)
    hits = 0; N = 12
    for s in range(100, 100 + N):
        w = build_seed_world(seed=s); w.run({}, T_CHARGE); replay(w, trace, T_CHARGE + res['depth'] + 2)
        hits += goal(w)
    print(f"robustness: witness reaches goal under {hits}/{N} fresh seeds")
    ok &= hits == N

    # 3. function test: the constructed element works; a world without the construction does not
    t = real.tick
    built = real.clone(); built.run({t: ([(AG, 'set', (10, 4))], ())}, t + 8)
    unbuilt = build_seed_world(); unbuilt.run({}, t); unbuilt.run({t: ([(AG, 'set', (10, 4))], ())}, t + 8)
    pushed = lambda w: any(a == ('push', (7, 6), (7, 7)) for ev in w.log[t:] for a in ev['acts'])
    print(f"function: signal -> constructed C'-A' element pushes the object: built={pushed(built)}, unbuilt control={pushed(unbuilt)}")
    ok &= pushed(built) and not pushed(unbuilt)

    # 4. the constructed element persists: bonded, and survives 200 ticks of thermal noise with the seed idle
    later = real.clone(); later.run({}, real.tick + 200)
    print(f"persistence: target bond present after 200 idle ticks = {TARGET_BOND in later.bonds}; ledger {later.energy()}")
    ok &= TARGET_BOND in later.bonds

    print("\nI1 (Claim 1, seeded construction of a second functioning element):", "ESTABLISHED" if ok else "NOT ESTABLISHED")
    return ok


def negative():
    """Unreachable goal: A' facing N at (7,5). No seed arm rotates (8,5) or (7,5). Expected: NOT_ESTABLISHED, exhausted."""
    seed = build_seed_world(); seed.run({}, 20)
    sites = [s for s in seed.authorized_sites(AG) if s != (10, 4)]
    def g(w):
        pt = w.grid.get((7, 5)); return bool(pt) and pt.sp == 'A' and pt.o == 'N'
    res = oracle_o2(seed, sites, g, max_depth=7, max_nodes=150_000)
    print("negative control:", {k: v for k, v in res.items() if k != 'trace'})
    return res['status'] == 'NOT_ESTABLISHED' and res['reason'] == 'exhausted'


if __name__ == '__main__':
    ok = main()
    if '--negative' in sys.argv: ok &= negative()
    sys.exit(0 if ok else 1)
