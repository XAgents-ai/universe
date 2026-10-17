# Universe V0 — Physics Specification

*For the author's family, and the generations after them. May what is built here outlast its builders and be of use to those who come next.*

**Revision:** R0.3, 2026-10-17. Supersedes R0.2, with the unchanged live seeded kernel semantics, a distinct deterministic cold-oracle conflict policy, and a working shared-world service. See `UNIVERSE_V0_PHYSICS_SPEC_R0_2.md` for the archived revision and its historically withdrawn claims. Companion code: `v0_kernel.py` (reference kernel, R0.2), `v0_kernel_r0.py` and `v0_kernel_r01.py` (archived for regression), `v0_acceptance.py` (I2–I5), `v0_memory_witness.py` (retained state), `v0_regression.py` (the four review findings), `v0_oracle.py` (ConstructionOracle O2 + the first seeded construction witness).
**Rule set:** R0.3, illustrative. The live transition uses R0.2's seeded conflict resolution; the bounded oracle uses a *declared canonical-conflict cold variant*. No universality or open-ended evolution result is claimed.

## 0. What is and is not established

| Claim | Status | Evidence |
|---|---|---|
| Energy and matter are conserved on every permitted transition, **including every boundary intervention** | **Checked**: ledger asserted inside the kernel every tick; 12,000 fuzzed ticks over 40 random worlds; regression F1 (remove/replace of charged, excited and bonded matter) | I5, `v0_regression.py` |
| Execution is deterministic and replayable from log + seed; the state hash is a complete identity | **Checked**: 60/60 hashes; hash distinguishes sources, authorization and RNG state | I3, F3 |
| The oracle's material search key is future-determining for the **canonical-conflict cold variant**, including periodic source phase; seeded worlds distinguish RNG states | **Checked in F5/F6 regressions**. This is not a proof for exhaustiveness over all stochastic live-world outcomes. | F5, F6 |
| External agents can only write, claim or observe charged control sites; authority never spreads by welding | **Checked**: unauthorized and unknown ops refused before any charge; two owners' welded clusters share nothing; `claim` is explicit, exclusive, charged | I2, F2, F4 |
| A hand-placed sensor→gate→mover machine does environmentally responsive work with zero agent input after disconnect; response causally mediated by its sensor path | **Checked** via four counterfactual clones | I3, I4 |
| R0.1 supports retained state with no memory primitive (write, hold ≥80 ticks, non-destructive read, erase) | **Checked**, hand-placed configuration (O1) | `v0_memory_witness.py` |
| **I1 (Claim 1):** from ordinary seed manipulators and loose matter, an agent physically assembles a functional bonded responder using charged writes | **Established for directly coupled P–A responder**: 205 generated successor attempts, three writes, 12/12 fresh-seed replays, four post-disconnect controls plus an unbuilt initial-world control. Separate C–A witness retained. | `v0_responder.py`, `o2_witness_autonomous_responder.json` |
| The oracle reports bounded failure honestly | **Checked** in a small, fully completed canonical-cold negative test at horizon 4 (8 generated successors). The R0.2 depth-7 result of 21,695 generated successors and its predecessor 14,375 are **historical, not certified under R0.3**: F6 invalidated stochastic future-equivalence. | `test_oracle_bounded_negative.py` |
| **Claim 2:** an actuator arises from raw matter with no pre-existing actuator | **Not claimed.** Not an I1 requirement (§9). | — |
| Direct physical sensor–actuator (P–A) constructed from seed responds after controller disconnection | **Established** with physical bonded assembly and environmental intervention. Full P–C–G–C–A responder construction still open. | `v0_responder.py` |
| R0.1 is Turing-universal; wire crossing is constructible | **Not claimed.** | — |

## 1. Frozen decisions this spec implements

1. One control interface: every controller (external model, program VM, physical matter) acts through material control sites.
2. Entry actuators are ordinary material configurations.
3. External control is charged in world energy; the external model injects no energy and edits no matter.
4. Thermal energy is tracked, conserved, and non-recoverable in V0.
5. Constructibility is established by bounded search with witness traces, never by assertion.
6. Integer arithmetic, canonical synchronous update, seeded conflict resolution, reproducible logs.

**Change in R0.3 (F6).** The real/live kernel retains seeded proposal shuffling. The bounded oracle calls `Params.cold()`, which disables thermal fluctuations *and explicitly changes proposal conflict selection to a canonical ordering*. Thus the oracle explores one deterministic, declared variant, not every stochastic schedule. Its material search key includes source phase and parameters; in seeded or thermal-active mode the key additionally includes RNG and heat state. Existing R0.2 depth-7 exhaustion claims must be withdrawn until re-run within a soundly defined model. A positive witness remains valid when replayed with the real seeded kernel. A new seeded construction witness physically assembles a P→A autonomous responder. The HTTP viewer and open-universe API are local research prototypes, not evidence of a discovered civilization or cumulative ratchet.

**Historical change in R0.2 (response to the viewer author's finding).** F5: `physical_key()` omitted the phase of periodic energy sources, so two identical configurations at different ticks mod period were merged although their futures differ. The key now includes `tick mod lcm(periods)`. Every exhaustion claim made under R0.1 is re-run and re-stated here; witnesses were never affected (a witness is a valid trace whatever the key).

**Changes in R0.1 (response to the independent review of the implementation).** F1: boundary matter ops export the energy they carry. F2: authorization is per-particle and acquired only by explicit, exclusive, charged `claim`. F3: the state hash is a complete identity; a separate `physical_key` serves the cold oracle. F4: `replace` = remove + drop; unknown ops are refused before any charge, with logged reasons. New species R (rotator) so orientation of raw parts is reachable rather than a gift. I1 is resolved as Claim 1 (seeded construction). The ConstructionOracle is implemented.

## 2. `WorldState`

```
WorldState :=
  W, H            : int            lattice extent; cells (x,y); 4-neighbourhood; hard boundary
  grid            : cell -> Particle | ∅      at most one particle per cell
  heat            : cell -> ℕ      thermal quanta per cell
  bonds           : set{ {c1,c2} } unordered pairs of adjacent occupied cells
  sources         : cell -> (dir, period)     world-owned energy inputs; a source cell holds no particle
  auth            : agent -> set{pid}         control sites each agent owns; a pid has at most one owner
  next_pid        : ℕ              particle identities are never reused
  tick            : ℕ
  E_in, E_out     : ℕ              cumulative boundary energy transfers
  M_in, M_out     : species -> ℕ   cumulative boundary matter transfers
  seed, rng state

Particle := (sp, o, x, q, c, seen, pid)
  sp   ∈ {S, C, G, A, W, B, P, K, R}      species, conserved; no transmutation in V0
  o    ∈ {N, E, S, W}                   orientation (meaningful for C, G, A, W, P, K, R)
  x    ∈ {0,1}   held excitation quantum          (C, G)
  q    ∈ [0, Q_MAX]  stored quanta                (B)
  c    ∈ {0,1}   control bit                       (K)
  seen ∈ {0,1}   edge-detector memory              (P)
  pid  ∈ ℕ       stable identity
```

Geometry: `ahead = p + o`, `behind = p − o`, `left = rotate_ccw(o)`, `right = rotate_cw(o)`.

**State identity.** `state_hash()` covers grid (with pids), bonds, heat, sources, auth, accounts, params, lattice size, tick, and RNG state. The *material* `physical_key()` includes grid, bonds, sources, auth, params, dimensions, and source phase `tick mod lcm(periods)`. With `Params.cold()` it can omit heat and RNG because heat cannot affect material behavior and proposal conflicts are canonically ordered. With seeded proposal order or thermal dynamics, it **includes** heat and RNG. Search-key equivalence is scoped to the declared transition variant and permitted agent inputs; it is not an equivalence for arbitrary future experimental boundary interventions.

## 3. `RuleSet` R0.1 — species

| Sp | Name | Role | Energy behaviour |
|---|---|---|---|
| S | structural | inert; frames, raw material, objects to move | none |
| C | conductor | carries one excitation one cell per tick in direction `o` | lossless hop |
| G | gate | OR of side inputs, vetoed by a quantum from behind; 1-tick delay | consumes inputs; emits ≤1 |
| A | mover | when triggered, pushes the free particle ahead by one cell | trigger → heat |
| R | rotator | when triggered, rotates the free particle ahead 90° clockwise | trigger → heat |
| W | welder | when triggered, toggles the bond between the two cells ahead | trigger → bond, or bond+trigger → heat |
| B | store | holds up to Q_MAX quanta; the only usable-energy reservoir | passive |
| P | sensor | emits a pulse when the cell ahead becomes occupied | 1 quantum from an adjacent B |
| K | control site / powered emitter | the only thing a controller can write; on `c=1`, emits 1–2 fresh quanta from an adjacent B | 1 per emitted quantum |

Parameters: `Q_MAX=8, E_BOND=1, k_loss=0.01, k_break=0.01, k_diff=0.02, p_heat=0.6, obs_radius=3`. `Params.cold()` sets `k_loss=k_break=k_diff=0`, sets `conflict_policy="canonical"` and leaves heat transport and radiation on. `Params()` defaults to `conflict_policy="seeded"`.

Design intent: wire, gain, veto, store, sensing, pushing, rotating and bonding are primitives; memory, oscillation, fan-out, logic and every machine are compositions. K is one-shot (no latch primitive); G is memoryless.

## 4. `Transition` — the canonical tick

One tick maps `(WorldState, agent_ops, env_ops) → WorldState`. Phases run in order; each reads the state left by the previous one. Iteration is over sorted cells; all randomness comes from the seeded generator in a fixed call sequence.

**Phase 1 — boundary energy.** For each source `(s, d, τ)` with `tick mod τ = 0`, `t = s+d`: a C with `x=0` gets `x←1`, a B with `q<Q_MAX` gets `q+=1`; either way `E_in += 1`. Otherwise nothing. Sources are the only energy inputs.

**Phase 2 — boundary matter (experiments only, logged).** `drop(cell, sp, o)` into a free cell: `M_in += 1`. `remove(cell)`: the particle is **exported** — its `x + q` plus `E_BOND` per bond it held go to `E_out`, its bonds are deleted, `M_out += 1`, and if it was a control site it leaves every owner's `auth`. `replace(cell, sp, o)` = remove then drop. Every export is logged with the energy it carried.

**Phase 3 — external control.** For each `(agent, op, cell)`, in order: refuse `op ∉ {set, observe, claim}`; refuse if `grid[cell]` is not a K; for `claim`, refuse if the K already has an owner, or if no particle in its bonded cluster is a site the agent owns; for `set`/`observe`, refuse if the agent does not own that K. Only then draw one quantum from a B adjacent to the K (refuse `no-energy` if none); deposit it as heat at the K. Then `set`: `c ← 1`; `claim`: `auth[agent] ∪= {pid}`; `observe`: return the local view (§7). Every refusal is logged with its reason; a refused op costs nothing.

**Phase 4 — proposals** (from the post-phase-3 state; a proposal `(src, tgt, new?)` carries one quantum):
- C or G with `x=1`: `tgt = ahead`, `new=false`.
- K with `c=1`: `c ← 0`. For `tgt` in `[ahead, left]`: if `is_acceptor(tgt, src)` and a quantum can be drawn from an adjacent B, draw it and propose `new=true`.
- P: `seen' = [ahead occupied]`; if `seen' ∧ ¬seen`, `tgt = behind`, propose if acceptor and energy; `seen ← seen'`.

`is_acceptor(tgt, src)`, `rel` = direction from `tgt` to `src`: C: `x=0` · G: `rel ∈ {left, right, behind}` · B: `q<Q_MAX` · A, W, R: true · K: `rel ∈ {behind, right}` · S, P, empty, out-of-bounds: false.

**Timing rule.** A K written in phase 3 emits in phase 4 of the same tick; a C excited in tick *t* delivers in tick *t+1*; an actuator triggered in tick *t* acts in tick *t*. A C holding `x=1` cannot vacate and accept in the same tick, so a wire carries at most one quantum per two cells. Within a tick, effects apply in sorted target-cell order, which is why "rotate then push" needs the rotate written one tick earlier (the oracle found this; §9).

**Phase 5 — acceptance.** In the real/live kernel shuffle proposals with the seeded generator. In `Params.cold()` accept proposals in canonical sorted `(target, source, new)` order, a **declared oracle-only rule variant**. Capacity per tick: 1 for C, A, W, R; `Q_MAX−q` for B; unbounded for G and K. Accepted non-new proposals clear `src.x`. A blocked `new=false` proposal keeps its quantum at the source; a blocked `new=true` proposal dissipates it as heat at the source.

**Phase 6 — effects at targets.**
- C: `x ← 1`. B: `q += n`.
- G: `inh` = arrivals from behind, `sig` = from sides. If `inh>0 ∨ x=1 ∨ sig=0`: all → heat. Else `x ← 1`, `sig−1` → heat.
- K: from behind `c ← 1`; from right `c ← 0`; each arriving quantum → adjacent B if room, else heat.
- A: if `ahead` holds an unbonded particle and `ahead+o` is a free cell, move it. Trigger → heat.
- R: if `ahead` holds an unbonded particle, `o ← rotate_cw(o)`. Trigger → heat.
- W: `p1 = ahead, p2 = ahead+o`. Both occupied and bonded: remove bond, `1+E_BOND` → heat. Both occupied, unbonded: add bond, trigger → bond energy. Else trigger → heat.

**Phase 7 — thermal (seeded).** Excitation loss `min(1, k_loss·T)`; bond breaking `min(1, k_break·max T)`, `E_BOND` → heat; unbonded particles hop with `min(1, k_diff·T)`; heat quanta hop with `p_heat`; boundary cells with `T>0` radiate one quantum to `E_out`.

**Phase 8 — ledger and log.** Assert the invariants (§5); `tick += 1`; append the event record (§11) with the state hash.

Locality: every rule reads and writes the cell, its 4 neighbours, and for A/W/R the cell two ahead. No rule inspects whether an arrangement is a machine.

## 5. Energy accounting

| Account | Definition | Grade |
|---|---|---|
| `E_q` | Σ q over B | usable (K and P draw from it) |
| `E_x` | Σ x over C, G | usable in flight |
| `E_b` | `E_BOND·|bonds|` | stored, not usable: a cut bond releases to heat only |
| `E_T` | Σ heat | unusable |
| `E_in` | Σ source absorptions | boundary in |
| `E_out` | Σ radiated quanta **+ Σ energy carried by exported matter** | boundary out |

Invariant, asserted every tick: `E_q + E_x + E_b + E_T + E_out − E_in = const`. Matter, per species: `count + M_out − M_in = const`.

Usable energy for experiment matching: `X = E_q + E_x`, reported per cell. `E_b` is organisation, not resource, and is reported separately. Qualification B holds across boundary interventions (F1): nothing leaves the account except through `E_out`, and the log says what it was.

## 6. `Actuator`

Any bonded cluster containing ≥1 K with an adjacent B. The **seed (entry) actuator** issued at arrival is such a cluster, placed as ordinary matter, subject to phase 7 like everything else. Its material composition is on file (the `build_*` functions are the composition). It is an initial condition: V0 does not claim it built itself (§9, Claim 2).

Control sites are K particles. A controller of any kind can only set `c`.

## 7. `AgentBoundary`

| Request | Precondition | Cost | Returns |
|---|---|---|---|
| `observe(K)` | owned K; adjacent B with `q≥1` | 1 quantum → heat | species, orientation, `x`, `q` within Chebyshev radius `obs_radius`. Not bonds, heat, pids, or others' control bits. |
| `set(K)` | owned K; adjacent B with `q≥1` | 1 → heat, plus 1–2 at emission | ok / refused:reason / refused:no-energy |
| `claim(K)` | K has no owner; some particle in K's bonded cluster is a site the agent owns; adjacent B with `q≥1` | 1 → heat | ok / refused:owned / refused:not-bonded-to-own-site |

Ownership is per particle (pid), exclusive, and lost only when the particle is exported. Welding two agents' clusters transfers nothing (F2). To use a K you built: bond it to your cluster, then claim it; an unclaimed K bonded to your cluster can be claimed by anyone whose cluster it also touches, first claimant wins — possession is a physical act. Nothing grants one agent another's sites.

Information bound: at most one bit per owned K per tick, each costing ≥2 quanta. No text channel, no `create_*`, no matter edit, no energy grant. The LLM's compute, latency and energy are not modelled; phase 3 is the entire coupling.

## 8. Autonomous machine (the milestone object)

Definition: a bonded configuration M such that, over a registered interval with no agent owning any site, M performs an environmental-response function F — a specified change of world state conditional on a specified environmental event — on world-owned energy, and F is abolished by a registered intervention on M's internal sensor-to-actuator path but not by an unrelated intervention.

R0.1 witness (hand-placed): source→B→P → C → G(veto from an agent-writable K while connected) → C → A on a free S. Checked after disconnect with four clones.
R0.1 memory witness (hand-placed): ring `K → C×5 → G → C×3 → K`, interior source, reader line off K's second output into a counter B, writer `K_w→C→ring`, eraser `K_e→C→G.behind`. Write / hold 80 / read 8 / timed erase / mistimed-erase control all pass. Two ring bonds broke thermally in 135 ticks: maintenance is a real cost.

## 9. `ConstructionOracle`

**I1 is Claim 1.** The review was right that the original O2 statement had a bootstrapping problem. Two claims are distinguished:

- **Claim 1** (I1): from a pre-existing seed actuator — an initial condition with verified composition, obeying ordinary physics — an agent constructs another functioning element using only phase-3 ops. *Established* for a two-part element; *open* for the autonomous responder.
- **Claim 2**: an actuator arises from raw matter with no actuator and no privileged process. Not an I1 requirement; not claimed; a separate, harder research question.

**Obligations** per configuration-function pair `(X, F)`:
- **O1 — function.** A configuration `X` and a registered executable test `T_F` (inputs, predicate, horizon) that `X` passes under replay. `v0_acceptance.py`, `v0_memory_witness.py` and the function test in `v0_oracle.py` are O1 artefacts.
- **O2 — reachability.** From a declared initial state `I` (seed actuator, loose inventory, sources), a sequence of phase-3 ops reaching a state containing `X` with its bonds. The trace is the witness and satisfies I2 by construction.

**Algorithm as implemented** (`oracle_o2`): breadth-first search over ticks; at each tick one op from `{set K_i for owned K} ∪ {wait}`; children generated by `World.clone().step()` under `Params.cold()`; visited set keyed by `physical_key()`; bounds `max_depth` (ticks) and `max_nodes`. BFS returns the shortest witness in ticks within the model. Failure is reported as `NOT_ESTABLISHED` with `reason ∈ {exhausted, node-cap}` and the bounds — never "impossible". Minimum-size claims require `reason = exhausted` at every smaller size.

Canonical cold mode makes material-state equivalence sound under the oracle's restricted inputs and transition variant: random heat transport remains but cannot affect matter. This is **not** exhaustive search over the original seeded-conflict physics; F6 exposed that earlier overclaim. A found witness is then **replayed under real params** from the same initial state and across ≥12 fresh seeds; the success rate is the robustness report. Best-first variants may be used for finding, not for exhaustion claims.

**First seeded construction witness** (`v0_oracle.py`). Seed: welder arm, two mover arms, a rotator arm, and a signal arm (test only), each `source→B–K–C–X`, all bonded; loose inventory: a C mis-oriented (E), an A (S), a test object. Goal: `C(7,4)S` bonded to `A(7,5)S`. Result (R0.2 key): witness in 1,896 nodes / 2.2 s — `set K_r @20, set K2 @21, set K1 @22, set K_w @23` — the search discovered that rotation must precede the push. (Under the R0.1 key the same witness was found in 1,196 nodes; the difference is ~700 states the old key wrongly merged.) Replay under real params: goal; 12/12 fresh seeds; signal into the constructed element pushes the object, the unconstructed control does not; the bond survives 200 idle ticks. **Archived R0.2 negative result, now withdrawn as a claim of exhaustive future equivalence:** the earlier script returned `NOT_ESTABLISHED / exhausted` at depth 7 after 21,695 generated successor attempts (R0.1 had reported 14,375). F6 showed that the seeded cold search key lacked the RNG state; this count is preserved as history, not accepted as a certified R0.3 exhaustion result. The completed R0.3 negative test is the small horizon-four canonical-cold test.

**Reachability geometry, a finding.** A straight-line pusher and a straight-line welder both need the in-line cell adjacent to the target; so for a bond between two cells, each part must enter *perpendicular* to the bond axis. This is a property of R0.1's manipulators, not of the search, and it is why the next milestone is harder than it looks.

**New R0.3 witness:** `v0_responder.py` starts from ordinary pre-placed construction arms, a world-owned source feeding a B adjacent to the eventual P, and loose P/A parts. Cold oracle finds 3 charged writes in 4 ticks after examining 205 generated successor attempts: P and A are physically moved into adjacent cells and welded. The resulting P→A configuration senses an adjacent matter drop and pushes a particle with no external agent input. O1 includes wrong-cell, quiet, and sensor-removal controls; 12/12 replay seeds pass. The initial seed arms are not claimed to arise spontaneously.

**Next construction milestone:** a full multi-component P→C→G→C→A responder, with the physical controller and necessary stores assembled from seed; then multi-entrant physical inheritance with causal ablations.

## 10. Universe family (generator)

A rule set is a point in a declared parameter space; R0.1 is one point. Varied per run with §4's structure fixed:
- which species carry which of {conduct, gate, move, rotate, weld, store, sense, emit}; 1–2 roles per species, or a role requiring two species in contact
- input/output adjacency geometry; element delays (1–3 ticks); wire capacity rule
- `Q_MAX, E_BOND`, per-role energy prices, source periods and density
- thermal constants; boundary radiation rate
- sensor predicate (presence / absence / charged-store / heat-above-threshold)
- manipulator semantics: single-cell push (R0.1) / run push / sliding with per-cell cost

Pipeline per sample: static ledger check per rule → I5 fuzz → oracle O1+O2 for the four functions below → log accept/reject with reasons → for accepted pairs, replay rule set 1's witnesses in rule set 2 and report per function: works / works at different cost / fails. Non-transferable pairs serve Experiment 2; transferable pairs serve repair and invariant studies. The role whitelist excludes composites (no latch species, no oscillator species).

| Function | Test |
|---|---|
| retained state | write / hold ≥50 / read / erase |
| signal over distance | a pulse traverses ≥L cells within tolerance |
| conditional control | output iff A present and B absent |
| active element | a constructed cluster converts source energy into displacement on a cue |

## 11. `EventLog`

Per tick: `tick, ruleset_id, seed, agent_ops (with result/reason), env_ops, boundary exports (with energy carried), n_blocked, acts (push/rotate/weld/cut), energy accounts, matter accounts, state_hash`. Initial state and parameters once. Replay = kernel + initial state + the op columns + seed; hashes match tick-for-tick (I3). A re-seeded run is a different experiment.

## 12. `ExperimentHarness`

`World.clone()` is a full deep copy including RNG state; counterfactuals are clones diverging only by registered `env_ops`.

| Condition | Fabrication | Control | On this kernel |
|---|---|---|---|
| A | schema | executable | `place_schema` env-op at declared material+energy cost; VM writes `c` on the cluster's K each tick |
| B | schema | physical | `place_schema` only |
| C | physical | executable | VM may write `c` on owned K |
| D | physical | physical | the kernel as specified |

Capability measure `R(W, B)`: a fresh agent with budget `B` (ticks, phase-3 ops, drawable quanta) enters a world where predecessors performed cumulative work `W` (Σ quanta drawn in phases 3–4 by prior agents). `R` is its score on the registered probe set (§10's four functions plus signal-across-N and move-object-to-cell). Counterfactuals: intact / organisation disrupted by cutting bonds with per-cell `X` matched / information-only / transplant.

## 13. Acceptance tests — mapping and results (R0.2)

| Invariant | Executable check | Result |
|---|---|---|
| I1 constructible (Claim 1) | O2 witness from seed; replay; 12-seed robustness; post-disconnect response | **pass for direct P–A responder**; full gated responder open |
| I2 bounded authority | only `set/observe/claim`; unauthorized, unknown, unowned refused before charge | pass |
| I3 autonomous continuation | zero agent ops after disconnect; 60/60 hashes | pass |
| I4 environmental response | respond / wire-cut / wrong-cell / quiet | pass |
| I5 energy integrity | kernel assertion every tick; 12,000 fuzzed ticks; F1 interventions | pass |
| retained state (O1) | write / hold / read / erase / mistimed control | pass |
| review findings F1–F6 | F1–F5 pass in original regression; F6 demonstrates seeded counterexample and canonical-cold resolution | pass for specified tests |
| oracle honesty | canonical-cold restricted negative: horizon 4, 8 generated successors; historical depth-7 claim withdrawn until sound re-run | pass for restricted test |

Run: `bash run_checks.sh`. The old `v0_oracle.py --negative` depth-7 search is **not** part of acceptance: it was reported under an incomplete R0.2 search key and has not been exhaustively re-certified under the canonical cold variant.

## 14. Explicitly not modelled in V0

Kinetic energy, momentum, gravity, rigid-body motion (a push moves one free particle one cell; bonded clusters never move). Heat engines. Species transmutation. Continuous space, 8-neighbourhood, periodic boundaries. The external model (compute, latency, memory, energy, internal language). Information-theoretic thermodynamics (the per-bit charge is an operational assumption). Any notion of a constructed actuator having a new mind: ownership is by `claim`, nothing more.

## 15. Known weaknesses of R0.3

1. **Wire crossing** in 2D is an open oracle target; if unconstructible, planarity caps what can be built.
2. **Welder toggles**; a sampled rule set may split bond/cut.
3. **P senses presence only**; other predicates are generator variables.
4. **Half-rate wires** (no vacate-and-accept).
5. **Single-cell push** makes construction a packing puzzle (§9's geometry finding). A run-push or sliding manipulator is a family variable worth sampling early.
6. **Maintenance is unmodelled as a behaviour**; the probe set should include persistence-under-heat so the burden is measured.
7. **K's second output** will deposit into a store placed on its left, a wasteful no-op; place stores on a K's right or behind.
8. **Claim is first-come**: an agent that builds a K and delays claiming it can lose it to a neighbour whose cluster touches it. Deliberate — possession is physical — but it should be stated to agent authors.

## 16. Participation: observers, human agents, experimenters

The kernel has exactly two ways to affect the world — phase 3 (owned control sites, charged) and phase 2 (registered boundary ops, logged, experiments only). Participation is defined on those two and nothing else.

| Experience | Mechanism | Can change the world? | Information |
|---|---|---|---|
| Observer | reads `WorldState`, `EventLog`, replays | **no** — read-only, not a third way to act | global |
| Participant (human or AI) | owns an entry actuator; phase 3 only | yes, under physics | paid, local (`observe`) |
| Experimenter | phase 2 on an isolated research clone | yes, as logged boundary transfers | global |

Rules:
1. **One physics.** A participant is a participant; the kernel does not know, and must not be told, what kind of mind owns a control site. Same costs, same radius, same refusals. There is no human-only or AI-only op.
2. **No gods.** Nobody edits a cell in the open universe. A phase-2 op exists only in research clones and appears in the ledger as matter and energy crossing the boundary.
3. **Information is a condition, not a sin.** A participant whose controller also had the observer's global view is a different experimental condition from one with local observations only. It is not forbidden; it is labelled. Record `controller ∈ {human, model, program}`, **prior training/exposure to the rule set**, and whether the participant **accessed global state for this particular live instance**, separately. `global_exposure_declared` in the local HTTP interface is self-attested, not proof of blinding. General pretrained engineering knowledge is not the same causal condition as having access to current hidden world state.
4. **No language channel between participants.** Humans and models communicate through the world or not at all; anything they invent in matter is theirs.
5. **The viewer renders state and ledger, never labels.** It may draw particles, bonds, quanta, heat, sources, ownership and replays. It draws a box called "machine" only where an acceptance test defined that machine. A participant's view is the paid `observe` result and nothing more; the observer's view is never routed to a participant's controller except as a declared `global-informed` condition.
6. **Early experiments keep human participants separately identified**, so human guidance is not mistaken for independent AI discovery. The eventual open universe need not.

## 17. R0.3 live implementation and boundaries

`open_world.py` creates a shared, persistent 22×15 lattice. There are four pre-placed, ordinary, world-owned seed-actuator entry sites; `join` grants one exclusive site from the finite initial inventory. Participants may be human/model/program controllers; the physics engine cannot distinguish them. Every live action advances one simulation tick through `World.step`; there is no independent wall-clock evolution or spontaneous population growth. The server persists each join/action in a hash-chained JSONL journal and verifies the complete `state_hash` when replaying after restart. No live endpoint accepts `drop/remove/replace`; those exist only in experiment clones. A live observer can inspect the global state but cannot change it; an actor token exposes only the actor's own authorized sites, paid local observations, and operation results. Observer access must be declared when used in controlled research, not considered morally forbidden.

The current browser is a local research viewer (not hardened for public deployment). Bearer tokens are stored in the journal on the local host; server-side joins are limited to four initial slots; a browser attempts to resume its participant token via session storage. The append-only journal is a deterministic audit trail, **not** a cryptographically signed external evidence service or crash-safe database transaction protocol. The in-memory session-based solo world and experiment worlds are deliberately separate from the shared universe. World progression occurs only when an actor sends a request.

A working physically assembled P→A responder and the older signal element are *constructibility* results, not proof of open-ended evolution, independent scientific discovery, a technological ratchet, or model intelligence emerging from physical dynamics. The full gated responder and the multi-generation inheritance experiment are still open.

## 18. Review priorities

1. Look for a remaining unmodeled state variable that changes future behavior but is absent from the canonical cold `physical_key()`. Confirm F5 and F6 without taking the oracle implementation on faith.
2. Check that the physical responder is assembled from free P/A parts using only permitted charged control-site actions, without creation APIs or an unreported manual intervention.
3. Check counterfactual causal attribution, time ordering, identical source budgets, thermal stochastic robustness, and the meaning of 'disconnect'.
4. Check exclusive ownership and the `claim` model against cross-agent construction/competition, and prove no live HTTP access to experimental boundary operations.
5. Audit information channels in viewer and HTTP responses, including token handling, journal replay, role isolation, and global-view provenance.
6. Do not promote results from the tiny P→A witness to construction of an arbitrary machine or a cumulative capability ratchet.

**Outstanding:** fully gated responder O2, generative chemistry family, real LLM controller integration, 3D substrate, scaling / crash recovery / authentication, pre-registered multi-generation R(W,B) experiments.

End of R0.3 specification.
