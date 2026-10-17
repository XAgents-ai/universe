"""
Universe V0 - reference kernel for candidate rule set R0.

Integer energy quanta, synchronous canonical update, seeded perturbations,
per-tick conservation ledger, reproducible state hashes, counterfactual cloning.

This is the executable companion to UNIVERSE_V0_PHYSICS_SPEC.md. It exists to
check invariants I2-I5 on a hand-placed machine and to fuzz the ledger. It does
NOT implement the construction oracle; constructibility claims in the spec are
therefore unverified until that oracle runs (see spec, section 9).
"""
from __future__ import annotations
import copy, hashlib, json, random
from collections import defaultdict
from dataclasses import dataclass

DIRS = {'N': (0, -1), 'E': (1, 0), 'S': (0, 1), 'W': (-1, 0)}
ORDER = ['N', 'E', 'S', 'W']
SPECIES = ['S', 'C', 'G', 'A', 'W', 'B', 'P', 'K']


def left(o):  return ORDER[(ORDER.index(o) - 1) % 4]   # counter-clockwise
def right(o): return ORDER[(ORDER.index(o) + 1) % 4]   # clockwise
def back(o):  return ORDER[(ORDER.index(o) + 2) % 4]
def add(p, o):
    d = DIRS[o]
    return (p[0] + d[0], p[1] + d[1])


@dataclass
class Particle:
    sp: str
    o: str = 'N'
    x: int = 0        # held excitation quantum (C, G only)
    q: int = 0        # stored quanta (B only)
    c: int = 0        # control bit (K only)
    seen: int = 0     # edge-detector memory (P only)


@dataclass
class Params:
    Q_MAX: int = 8
    E_BOND: int = 1
    k_loss: float = 0.01     # P(excitation -> heat) per unit local T
    k_break: float = 0.01    # P(bond -> heat) per unit local T
    k_diff: float = 0.02     # P(free particle hops) per unit local T
    p_heat: float = 0.6      # P(heat quantum hops) per tick
    obs_radius: int = 3


class World:
    def __init__(self, W, H, seed, params=None):
        self.W, self.H, self.seed = W, H, seed
        self.P = params or Params()
        self.rng = random.Random(seed)
        self.grid: dict = {}        # pos -> Particle
        self.heat: dict = {}        # pos -> int
        self.bonds: set = set()     # frozenset({p1, p2})
        self.sources: dict = {}     # pos -> (dir, period)   world-owned energy
        self.auth: dict = {}        # agent -> set(K positions)
        self.tick = 0
        self.E_in = 0; self.E_out = 0
        self.M_in = defaultdict(int); self.M_out = defaultdict(int)
        self.E0 = None; self.M0 = None
        self.log = []

    # ---------- geometry ----------
    def inb(self, p): return 0 <= p[0] < self.W and 0 <= p[1] < self.H
    def boundary(self, p): return p[0] in (0, self.W - 1) or p[1] in (0, self.H - 1)
    def nbrs(self, p): return [add(p, o) for o in ORDER if self.inb(add(p, o))]
    def T(self, p): return self.heat.get(p, 0)
    def addheat(self, p, n=1): self.heat[p] = self.heat.get(p, 0) + n
    def bonded(self, p): return any(p in b for b in self.bonds)
    def free_cell(self, p): return self.inb(p) and p not in self.grid and p not in self.sources

    # ---------- setup ----------
    def place(self, pos, sp, o='N', q=0):
        assert self.free_cell(pos), pos
        self.grid[pos] = Particle(sp, o, q=q)
    def add_source(self, pos, o, period):
        assert self.free_cell(pos), pos
        self.sources[pos] = (o, period)
    def grant(self, agent, kpos): self.auth.setdefault(agent, set()).add(kpos)
    def bond(self, p1, p2):
        """Setup-time bond between two occupied, adjacent cells (counted in E_b from tick 0)."""
        assert p1 in self.grid and p2 in self.grid and p2 in self.nbrs(p1), (p1, p2)
        self.bonds.add(frozenset({p1, p2}))
    def bond_path(self, cells):
        for a, b in zip(cells, cells[1:]): self.bond(a, b)

    def cluster(self, p):
        seen, st = {p}, [p]
        while st:
            u = st.pop()
            for b in self.bonds:
                if u in b:
                    v = next(iter(b - {u}))
                    if v not in seen: seen.add(v); st.append(v)
        return seen
    def authorized(self, agent, kpos):
        ks = self.auth.get(agent, set())
        return kpos in ks or bool(self.cluster(kpos) & ks)

    # ---------- accounts ----------
    def store_of(self, p):
        for n in self.nbrs(p):
            pt = self.grid.get(n)
            if pt and pt.sp == 'B': return pt
        return None
    def draw(self, p):
        s = self.store_of(p)
        if s and s.q > 0: s.q -= 1; return True
        return False
    def energy(self):
        Ex = sum(pt.x for pt in self.grid.values())
        Eq = sum(pt.q for pt in self.grid.values())
        Eb = len(self.bonds) * self.P.E_BOND
        ET = sum(self.heat.values())
        return dict(Ex=Ex, Eq=Eq, Eb=Eb, ET=ET, Ein=self.E_in, Eout=self.E_out,
                    total=Ex + Eq + Eb + ET + self.E_out - self.E_in)
    def matter(self):
        cnt = defaultdict(int)
        for pt in self.grid.values(): cnt[pt.sp] += 1
        return {s: cnt[s] + self.M_out[s] - self.M_in[s] for s in SPECIES}
    def state_hash(self):
        rep = dict(t=self.tick,
                   g=sorted((p, pt.sp, pt.o, pt.x, pt.q, pt.c, pt.seen) for p, pt in self.grid.items()),
                   b=sorted(tuple(sorted(b)) for b in self.bonds),
                   h=sorted((p, n) for p, n in self.heat.items() if n),
                   e=self.energy())
        return hashlib.sha256(json.dumps(rep, sort_keys=True, default=list).encode()).hexdigest()[:16]

    def observe(self, kpos):
        r = self.P.obs_radius
        view = {}
        for (x, y), pt in self.grid.items():
            if max(abs(x - kpos[0]), abs(y - kpos[1])) <= r:
                view[(x, y)] = (pt.sp, pt.o, pt.x, pt.q)
        return view

    # ---------- the tick ----------
    def is_acceptor(self, tgt, src):
        if not self.inb(tgt): return False
        pt = self.grid.get(tgt)
        if not pt: return False
        rel = next((o for o in ORDER if add(tgt, o) == src), None)
        if pt.sp == 'C': return pt.x == 0
        if pt.sp == 'G': return rel in (left(pt.o), right(pt.o), back(pt.o))
        if pt.sp == 'B': return pt.q < self.P.Q_MAX
        if pt.sp in ('A', 'W'): return True
        if pt.sp == 'K': return rel in (back(pt.o), right(pt.o))
        return False

    def step(self, agent_ops=(), env_ops=()):
        P, rng = self.P, self.rng
        ev = {'tick': self.tick, 'agent': [], 'env': list(env_ops), 'blocked': 0, 'acts': []}

        # 1. boundary energy: world-owned sources
        for spos, (o, period) in sorted(self.sources.items()):
            if self.tick % period == 0:
                pt = self.grid.get(add(spos, o))
                if pt and pt.sp == 'C' and pt.x == 0: pt.x = 1; self.E_in += 1
                elif pt and pt.sp == 'B' and pt.q < P.Q_MAX: pt.q += 1; self.E_in += 1

        # 2. boundary matter: registered environmental interventions (logged)
        for op in env_ops:
            if op[0] == 'drop':
                _, pos, sp, o = op
                if self.free_cell(pos): self.grid[pos] = Particle(sp, o); self.M_in[sp] += 1
            elif op[0] == 'remove':
                pt = self.grid.pop(op[1], None)
                if pt: self.M_out[pt.sp] += 1; self.bonds = {b for b in self.bonds if op[1] not in b}
            elif op[0] == 'replace':
                _, pos, sp, o = op
                pt = self.grid.pop(pos, None)
                if pt: self.M_out[pt.sp] += 1
                self.grid[pos] = Particle(sp, o); self.M_in[sp] += 1

        # 3. external controllers: only control-site writes, each charged
        for agent, op, pos in agent_ops:
            pt = self.grid.get(pos)
            if not pt or pt.sp != 'K' or not self.authorized(agent, pos):
                ev['agent'].append((agent, op, pos, 'refused')); continue
            if not self.draw(pos):
                ev['agent'].append((agent, op, pos, 'no-energy')); continue
            self.addheat(pos)                                   # write cost dissipated
            if op == 'set': pt.c = 1; ev['agent'].append((agent, op, pos, 'ok'))
            elif op == 'observe': ev['agent'].append((agent, op, pos, 'ok', self.observe(pos)))

        # 4. proposals, computed from the pre-tick state
        props = []
        for pos, pt in sorted(self.grid.items()):
            if pt.sp in ('C', 'G') and pt.x == 1:
                props.append(dict(src=pos, tgt=add(pos, pt.o), new=False))
            elif pt.sp == 'K' and pt.c == 1:
                pt.c = 0                                          # one-shot
                for tgt in (add(pos, pt.o), add(pos, left(pt.o))):
                    if self.is_acceptor(tgt, pos) and self.draw(pos):
                        props.append(dict(src=pos, tgt=tgt, new=True))
            elif pt.sp == 'P':
                seen = 1 if add(pos, pt.o) in self.grid else 0
                if seen and not pt.seen:
                    tgt = add(pos, back(pt.o))
                    if self.is_acceptor(tgt, pos) and self.draw(pos):
                        props.append(dict(src=pos, tgt=tgt, new=True))
                pt.seen = seen

        # 5. acceptance with seeded conflict order
        rng.shuffle(props)
        taken = defaultdict(int); accepted = []
        for pr in props:
            tgt, src = pr['tgt'], pr['src']
            pt = self.grid.get(tgt) if self.inb(tgt) else None
            ok = self.is_acceptor(tgt, src) if pt else False
            if ok and pt.sp == 'C': ok = taken[tgt] < 1
            if ok and pt.sp == 'B': ok = pt.q + taken[tgt] < P.Q_MAX
            if ok and pt.sp in ('A', 'W'): ok = taken[tgt] < 1
            if ok: taken[tgt] += 1; accepted.append(pr)
            else:
                ev['blocked'] += 1
                if pr['new']: self.addheat(src)                  # drawn quantum dissipates
        for pr in accepted:
            if not pr['new']: self.grid[pr['src']].x = 0
        by_tgt = defaultdict(list)
        for pr in accepted: by_tgt[pr['tgt']].append(pr['src'])

        # 6. effects at targets
        for tgt in sorted(by_tgt):
            pt, srcs = self.grid[tgt], by_tgt[tgt]
            if pt.sp == 'C': pt.x = 1
            elif pt.sp == 'B': pt.q += len(srcs)
            elif pt.sp == 'G':
                rels = [next(o for o in ORDER if add(tgt, o) == s) for s in srcs]
                inh = sum(r == back(pt.o) for r in rels); sig = len(rels) - inh
                if inh or pt.x == 1 or sig == 0: self.addheat(tgt, len(rels))
                else: pt.x = 1; self.addheat(tgt, len(rels) - 1)
            elif pt.sp == 'K':
                for s in srcs:
                    rel = next(o for o in ORDER if add(tgt, o) == s)
                    if rel == back(pt.o): pt.c = 1
                    elif rel == right(pt.o): pt.c = 0
                    st = self.store_of(tgt)
                    if st and st.q < P.Q_MAX: st.q += 1
                    else: self.addheat(tgt)
            elif pt.sp == 'A':
                ahead, beyond = add(tgt, pt.o), add(add(tgt, pt.o), pt.o)
                mv = self.grid.get(ahead)
                if mv and not self.bonded(ahead) and self.free_cell(beyond):
                    self.grid[beyond] = self.grid.pop(ahead); ev['acts'].append(('push', ahead, beyond))
                self.addheat(tgt)                                 # work is dissipated
            elif pt.sp == 'W':
                p1, p2 = add(tgt, pt.o), add(add(tgt, pt.o), pt.o)
                if p1 in self.grid and p2 in self.grid:
                    b = frozenset({p1, p2})
                    if b in self.bonds: self.bonds.remove(b); self.addheat(tgt, 1 + P.E_BOND); ev['acts'].append(('cut', p1, p2))
                    else: self.bonds.add(b); ev['acts'].append(('weld', p1, p2))   # quantum -> bond energy
                else: self.addheat(tgt)

        # 7. thermal step (seeded, reproducible)
        for pos, pt in sorted(self.grid.items()):
            if pt.sp in ('C', 'G') and pt.x and rng.random() < min(1.0, P.k_loss * self.T(pos)):
                pt.x = 0; self.addheat(pos)
        for b in sorted(self.bonds, key=lambda b: tuple(sorted(b))):
            p1, p2 = tuple(sorted(b))
            if rng.random() < min(1.0, P.k_break * max(self.T(p1), self.T(p2))):
                self.bonds.remove(b); self.addheat(p1, P.E_BOND)
        for pos, pt in sorted(list(self.grid.items())):
            if pos in self.grid and not self.bonded(pos) and rng.random() < min(1.0, P.k_diff * self.T(pos)):
                opts = [n for n in self.nbrs(pos) if self.free_cell(n)]
                if opts: self.grid[rng.choice(opts)] = self.grid.pop(pos)
        nh = defaultdict(int)
        for pos, n in sorted(self.heat.items()):
            for _ in range(n):
                nh[rng.choice(self.nbrs(pos)) if rng.random() < P.p_heat else pos] += 1
        self.heat = {p: n for p, n in nh.items() if n}
        for pos in sorted(self.heat):
            if self.boundary(pos) and self.heat[pos] > 0:
                self.heat[pos] -= 1; self.E_out += 1
        self.heat = {p: n for p, n in self.heat.items() if n}

        # 8. ledger (I5) and log
        e, m = self.energy(), self.matter()
        if self.E0 is None: self.E0, self.M0 = e['total'], m
        assert e['total'] == self.E0, f"ENERGY LEDGER VIOLATION tick {self.tick}: {e} vs {self.E0}"
        assert m == self.M0, f"MATTER LEDGER VIOLATION tick {self.tick}"
        self.tick += 1
        ev['hash'] = self.state_hash(); ev['energy'] = e
        self.log.append(ev)
        return ev

    def run(self, schedule, until):
        """schedule: {tick: (agent_ops, env_ops)}; returns list of state hashes."""
        hashes = []
        while self.tick < until:
            a, e = schedule.get(self.tick, ((), ()))
            hashes.append(self.step(a, e)['hash'])
        return hashes

    def clone(self):
        return copy.deepcopy(self)
