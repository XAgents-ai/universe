# Independent Adversarial Review Request — Universe V0 R0.3

**Role:** You are an independent researcher reviewing code, mathematical semantics, and experimental evidence. Do not accept the author's claim labels as facts. Run the code. Seek concrete counterexamples and separate sound results from unsupported generalization.

## Research intent

A persistent digital physical universe admits independent human, program, and external AI-model agents through the same paid local control-site interface. The long-run hypothesis is whether physically inherited organization can raise fresh entrants' reachable capability frontier under fixed budgets and controlled priors. **That ratchet is not yet tested.** We are establishing constructibility, autonomous response, and a common physical substrate first.

## Claims offered for review

**C1 — I1 bounded seeded construction:** `v0_responder.py` starts from hand-placed seed construction arms and *loose* P/A material, finds three charged writes via a cold canonical bounded oracle (205 generated successors), assembles a bonded P–A object, and demonstrates an environment-triggered push after external control ends. Four post-disconnect comparisons, one unbuilt baseline, and 12 fresh-seed seeded-real replays pass. The more complex P-C-G-C-A construction is **not** claimed.

**C2 — F6 scoped resolution:** In live `Params()` physics proposals conflict via seeded RNG; under `Params.cold()` their selection is canonical sorted (an explicitly different cold search variant). The cold `physical_key()` omits heat and RNG; the seeded real key includes both. Test both equivalence and divergence, with and without simultaneous contested signals. Determine whether *any other future-determining variable* is omitted from the canonical cold key. `test_f6_resolution.py` documents this distinction. The historical R0.2 depth-7 `NOT_ESTABLISHED/exhausted` claim is withdrawn as uncertified; a new small horizon-four negative is included.

**C3 — live world:** `open_world.py` builds four preplaced ordinary seed actuators, permits at most four mutually independent controllers to enter, and verifies a hash-chained action journal / physical state after restart. The same physical kernel applies to humans, models, and programs. Only participant operations can change the live world after initialization; experimental `drop/remove/replace` remain cloned-lab-only. Check both API routes and *indirect* side effects. API protection is local-prototype level, not production security.

**C4 — audit viewer:** `server.py` and `static/*` render particles, orientations, bonds, charge, heat, ledgers and physically replayed inputs. They do not infer 'machine' labels from shapes. Actor responses expose only previously paid local observations, own authorized sites and action outcomes. The live observer has read-only global visibility; the research scientist can intervene only on isolated experiment clones. Check indirect information leaks, DOM state, exports, and bearer-token exposure.

## Suggested review experiments

1. Construct two cold states with equal keys; try to force divergent material successors by changing heat distribution, RNG state, source periods/phases, action order, authentication ownership, particle IDs, reservations, controller requests, or accumulated accounts. Carefully state which inputs/search constraints apply.
2. Reproduce the P–A witness. Show exact source-to-work/heat accounting on all involved ticks and whether component material was genuinely moved/welded rather than hand-placed into its final assembled geometry. Test alternate seeds and interventions including a disconnection without a boundary edit.
3. Demonstrate a fabricated `claim` or `set` cannot cross an ownership boundary through bonding, position changes, stale IDs, pending signals, or response serialization. Check changes to user identity and repeated joins.
4. Have two independent HTTP clients join, observe, act and restart the server. Verify every journal event reproduces with the original seed, including both participant IDs and energy state. Simulate a crash midway through a journal append and assess atomicity limits.
5. Trace an unauthorized participant operation through endpoint, service and kernel. Verify no role can invoke boundary interventions on the live world by an alternate path.
6. Search for cases where a rendered audit label attributes more than the state supports, and where a participant response exposes current global state or another actor's private observation.
7. Try adversarial high-rate calls and malformed request bodies. State explicitly what a localhost-only prototype guarantees and what it does not.
8. Check that the new cold canonical oracle does not accidentally claim exhaustive coverage of the seeded live dynamics; distinguish generated successors from unique states.

## Mandatory findings format

For each finding report `ID`, `severity`, `claim affected`, `concrete witness / failing test`, `mechanism`, `smallest correction`, and `which prior results need withdrawal or rerun`. If no error found in a section, state what you tested rather than declaring the whole design proven.

At the end, produce a table with **Established / Partially established / Not established** for (a) kernel conservation, (b) bounded constructibility, (c) post-disconnect autonomous response, (d) equivalent human/model physical authority, (e) persistence, (f) physical ratchet across independent generations, and (g) public Internet security. Do not mistake README assertions for evidence.

Start with:

```bash
python -m pip install -r requirements.txt
bash run_checks.sh
```

Optional headless browser (if installed Chromium at `/usr/bin/chromium`): `WITH_BROWSER=1 bash run_checks.sh`.
