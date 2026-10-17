# Universe V0 R0.2 — independent review (2026-10-17)

## Verified in this review

- `python v0_regression.py` passes F1–F5. Archived R0.1 fails F5.
- `python test_oracle_phase_key.py` passes: phase-sensitive search key distinguishes period-2 source phases.
- `python v0_oracle.py` reconstructs the two-part C–A construction witness in **1,896 generated successor attempts**, depth 5. Real-params replay passes; 12/12 fresh-seed replays succeed, the signal operates the constructed element, and its bond persists for the observed idle interval.
- `python v0_acceptance.py` passes I2–I5 checks and 12,000 fuzzed ticks. The script's historical disclaimer about construction-oracle absence refers specifically to its hand-placed *full responder*, not the separate two-part O2 witness.
- `python v0_memory_witness.py` passes its write/hold/read/erase checks.
- `python test_viewer_api.py` passes all three role-boundary checks; `python test_viewer_ui.py` reported zero JavaScript errors.

## Open review finding F6: cold search key aliases distinct futures

`python test_f6_rng_key.py` FAILS on R0.2 *by design*.

Even with `Params.cold()` there is an RNG-shuffled conflict-resolution phase (phase 5). Two cold worlds with three C particles arranged as two competing excitations towards one target, identical material state and source phase, but seeds 1 and 5, have identical `physical_key()` values and divergent physical state after a single tick. Cold heat transport also consumes random values and depends on heat state omitted by the key.

Consequence: positive O2 witness is valid; exhaustive negative reachability over unique future behaviors under the real cold rules has **not** been proved. Do not infer the specific negative goal is reachable; the example only invalidates the pruning equivalence.

Possible design routes: use an exact future-determining key including RNG and heat (costly); explicitly define deterministic canonical cold oracle conflict semantics (a different model); or branch on possible conflict outcomes.

## Reporting nuance: 'nodes' is not unique states

`v0_oracle.py` increments `nodes` before testing membership in `seen`. Thus the reported **1,896** and **21,695** are generated successor attempts/transitions, **not unique visited world states**. Log both `generated_successors` and `unique_state_keys` to avoid ambiguity.

The R0.2 specification reports 21,695 generated successors for the negative depth-7 run. The reviewer's attempt to reproduce this complete negative run exceeded its execution budget; that number remains **reported by the specification, not independently reproduced here**.

## Participation: prior knowledge vs current global observation

An LLM's general training prior about human engineering does not grant access to hidden, *current*, instance-specific global universe state. A human's access to a global audit viewer is a distinct information channel. Suggested metadata: `controller_type`, `world_prior_exposure`, and `live_observation_access` (with observable provenance and time), rather than treating all LLMs and globally observing humans as a single `global-informed` condition.

## Viewer scope

- Observer/audit: immutable replay; only full view is read-only.
- Human agent: only kernel charged observe/set/claim, plus wait; observer's live global state is not exposed in agent API. Current payload also includes public map bounds and its own authorized K positions as enrollment metadata.
- Experimenter: separate clone, boundary ops only and recorded in ledger.
- The three viewer sessions are **separate instances**, not a single multiplayer shared world. No AI agents are connected. This is a local research prototype, not a public security-hardened service.

R0.2 source kernel is included unchanged. No attempt was made to silently 'fix' F6 in physics or oracle.
