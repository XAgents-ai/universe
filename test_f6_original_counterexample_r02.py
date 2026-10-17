"""F6 regression: a cold-mode key must distinguish states whose future diverges.

The current R0.2 key is known to FAIL this test. It includes periodic-source phase
but omits RNG state, despite RNG-controlled signal-conflict resolution.
"""
from v0_kernel_r02 import World, Params


def colliding_wires(seed):
    w = World(5, 5, seed, Params().cold())
    w.place((1, 2), 'C', 'E')
    w.place((2, 2), 'C', 'N')
    w.place((3, 2), 'C', 'W')
    w.grid[(1, 2)].x = 1
    w.grid[(3, 2)].x = 1
    return w


def main():
    a, b = colliding_wires(1), colliding_wires(5)
    before_same = a.physical_key() == b.physical_key()
    print('Initial physical_key identical:', before_same)
    a.step(); b.step()
    future_a = (a.grid[(1, 2)].x, a.grid[(2, 2)].x, a.grid[(3, 2)].x)
    future_b = (b.grid[(1, 2)].x, b.grid[(2, 2)].x, b.grid[(3, 2)].x)
    print('After one cold-mode tick: seed 1 =', future_a, '; seed 5 =', future_b)
    print('Future divergent:', future_a != future_b)
    sound = not (before_same and future_a != future_b)
    print(('PASS' if sound else 'FAIL'), 'F6 cold physical_key is future-determining')
    return sound


if __name__ == '__main__':
    raise SystemExit(0 if main() else 1)
