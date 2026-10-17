"""
Regression suite for the four kernel findings in the independent review of the R0 implementation.
Each test is a concrete counterexample. Run against R0.1 (v0_kernel) they must pass; run with
`python3 v0_regression.py r0` they execute against the archived R0 kernel (v0_kernel_r0) and are
expected to fail, which is the point of keeping it.
"""
import sys, importlib

K = importlib.import_module({'r0': 'v0_kernel_r0', 'r01': 'v0_kernel_r01'}.get(sys.argv[1] if len(sys.argv) > 1 else '', 'v0_kernel'))
World, Params, ORDER = K.World, K.Params, K.ORDER
AG, AG2 = 'agent-0', 'agent-1'


def t(name, fn):
    try:
        ok = fn()
    except Exception as ex:                      # an old kernel may crash rather than assert
        ok = False; detail = f"{type(ex).__name__}: {str(ex)[:80]}"
    else:
        detail = ''
    print(('PASS ' if ok else 'FAIL ') + name + (f'  [{detail}]' if detail and not ok else ''))
    return ok


def f1_remove_charged_store():
    w = World(6, 6, 1); w.place((2, 2), 'B', q=5); w.step()
    w.step(env_ops=[('remove', (2, 2))]); w.step()           # ledger assertion fires on R0
    return w.E_out >= 5


def f1_remove_bonded_particle():
    w = World(6, 6, 1); w.place((2, 2), 'S'); w.place((2, 3), 'S'); w.bond((2, 2), (2, 3)); w.step()
    w.step(env_ops=[('remove', (2, 2))]); w.step()
    return not w.bonds and w.E_out >= 1


def f1_remove_excited_wire():
    w = World(6, 6, 1); w.place((2, 2), 'C', 'N'); w.grid[(2, 2)].x = 1; w.step()
    w.step(env_ops=[('remove', (2, 2))]); w.step()
    return w.E_out >= 1


def f2_welding_does_not_transfer_authority():
    w = World(8, 8, 1)
    w.place((1, 1), 'K', 'E'); w.place((1, 2), 'B', q=4); w.grant(AG, (1, 1))
    w.place((3, 1), 'K', 'E'); w.place((3, 2), 'B', q=4); w.grant(AG2, (3, 1))
    w.place((2, 1), 'S'); w.bond((1, 1), (2, 1)); w.bond((2, 1), (3, 1))   # one bonded cluster, two owners
    w.step()
    ev = w.step(agent_ops=[(AG, 'set', (3, 1)), (AG2, 'set', (1, 1))])
    return all(a[3].startswith('refused') for a in ev['agent'])


def f2_claim_is_explicit_exclusive_and_charged():
    w = World(8, 8, 1)
    w.place((1, 1), 'K', 'E'); w.place((1, 2), 'B', q=4); w.grant(AG, (1, 1))
    w.place((2, 1), 'K', 'E'); w.place((2, 2), 'B', q=4)     # a built, unowned site bonded to AG's cluster
    w.bond((1, 1), (2, 1)); w.step()
    e1 = w.step(agent_ops=[(AG2, 'claim', (2, 1))])           # not bonded to AG2's site -> refused
    q_before = w.grid[(2, 2)].q
    e2 = w.step(agent_ops=[(AG, 'claim', (2, 1))])            # ok, charged
    e3 = w.step(agent_ops=[(AG2, 'claim', (2, 1))])           # owned -> refused
    e4 = w.step(agent_ops=[(AG, 'set', (2, 1))])              # now usable
    return (e1['agent'][0][3].startswith('refused') and e2['agent'][0][3] == 'ok'
            and w.grid[(2, 2)].q < q_before and e3['agent'][0][3] == 'refused:owned' and e4['agent'][0][3] == 'ok')


def f3_hash_distinguishes_sources_auth_rng():
    def mk(src, auth, rng_seed):
        w = World(6, 6, rng_seed); w.place((2, 2), 'K', 'E'); w.place((2, 3), 'B')
        if src: w.add_source((2, 4), 'N', 2)
        if auth: w.grant(AG, (2, 2))
        return w
    base = mk(False, False, 1).state_hash()
    return len({base, mk(True, False, 1).state_hash(), mk(False, True, 1).state_hash(),
                mk(False, False, 2).state_hash()}) == 4


def f5_search_key_includes_source_phase():
    """Same matter, different phase of a period-2 source: futures differ, so keys must differ."""
    def mk(t0):
        w = World(6, 6, 1, Params().cold())
        w.add_source((2, 1), 'S', 2); w.place((2, 2), 'C', 'S'); w.place((2, 3), 'B'); w.tick = t0
        return w
    a, b = mk(0), mk(1)
    ka, kb = a.physical_key(), b.physical_key()
    a.step(); b.step()
    futures_differ = a.grid[(2, 3)].q != b.grid[(2, 3)].q
    return futures_differ and ka != kb


def f4_replace_drops_old_bonds():
    w = World(6, 6, 1); w.place((2, 2), 'C', 'N'); w.place((2, 3), 'S'); w.bond((2, 2), (2, 3)); w.step()
    w.step(env_ops=[('replace', (2, 2), 'S', 'N')]); w.step()
    return not w.bonds


def f4_unknown_op_refused_without_charge():
    w = World(6, 6, 1); w.place((2, 2), 'K', 'E'); w.place((2, 3), 'B', q=4); w.grant(AG, (2, 2)); w.step()
    ev = w.step(agent_ops=[(AG, 'teleport', (2, 2))])
    return w.grid[(2, 3)].q == 4 and ev['agent'] and ev['agent'][0][3].startswith('refused')


def main():
    print(f"kernel: {K.__name__}")
    ok = True
    for name, fn in [
        ("F1 remove charged store exports its energy", f1_remove_charged_store),
        ("F1 remove bonded particle exports bond energy", f1_remove_bonded_particle),
        ("F1 remove excited wire exports the quantum", f1_remove_excited_wire),
        ("F2 welding two owners' clusters transfers no authority", f2_welding_does_not_transfer_authority),
        ("F2 claim is explicit, exclusive, charged", f2_claim_is_explicit_exclusive_and_charged),
        ("F3 state hash distinguishes sources / auth / rng", f3_hash_distinguishes_sources_auth_rng),
        ("F4 replace removes the old particle's bonds", f4_replace_drops_old_bonds),
        ("F4 unknown op is refused and not charged", f4_unknown_op_refused_without_charge),
        ("F5 oracle search key includes source phase", f5_search_key_includes_source_phase),
    ]:
        ok &= t(name, fn)
    print("REGRESSION:", "PASS" if ok else "FAIL")
    return ok


if __name__ == '__main__':
    main()
