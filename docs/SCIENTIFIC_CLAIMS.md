# Scientific claims ledger — initial baseline R0.3

Only executable evidence can raise a claim's status. A narrative, visual pattern, code comment or model assertion is not a physical-world observation.

| Claim | Current status | Main evidence / limitation |
|---|---|---|
| Particle, bond, control, heat and energy transition engine executes | Supported for tested R0.3 traces | `v0_kernel.py`; `v0_acceptance.py`, `v0_regression.py` |
| Tested events preserve the energy/matter ledger | Supported for tested transitions | Tick-level assertions and fuzz tests; **not** a mathematical proof for every conceivable input |
| Seeded simulation replay | Supported for tested traces | `v0_acceptance.py`, live journal verifier |
| Bound participant API and exclusive K ownership | Supported for tested paths | `v0_regression.py`, `test_live_world.py`, `test_viewer_api.py` |
| Hand-placed 1-bit retained state | Constructively functional O1 only | `v0_memory_witness.py`; **not** physically assembled from primitives |
| Seeded construction of C–A functioning element | O2 witness for specified initial condition | `v0_oracle.py`; cold search, replay under seeded physics |
| Seeded construction of autonomous P–A responder | O2 witness for specified initial condition | `v0_responder.py`; environment-sensitive behavior after disconnect, 12/12 fresh-seed replays |
| Full P–C–G–C–A autonomous responder physically assembled | **NOT ESTABLISHED** | Hand-placed O1 alone is insufficient |
| Exhaustive reachability in production seeded physics | **NOT ESTABLISHED** | R0.3 oracle searches a different canonical-conflict cold model |
| Heterogeneous LLMs interacting autonomously in one live world | **NOT ESTABLISHED** | HTTP supports program/model controllers, but no external model is shipped or running |
| Cumulative intergenerational physical ratchet R(W,B) | **NOT TESTED** | Requires independent entrants, matched controls and counterfactual inheritance tests |
| 3D universe, open-ended evolution, artificial life | **NOT CLAIMED** | Not represented or evaluated |

## Executable claim evidence IDs (required CI, advisory model reviews)

| Evidence ID | Registered executable check | Reported status |
|---|---|---|
| I5-R03 | `v0_acceptance.py` and `v0_regression.py` via `run_checks.sh` | Tested traces only |
| I3-R03 | `v0_acceptance.py` replay, `test_live_world.py` restart | Tested traces only |
| O2-PA-R03 | `v0_responder.py` in `run_checks.sh` | Seeded P–A witness only |
| T2-R04 | `test_journal_integrity.py::test_token_not_persisted` via direct script execution | Initial regression passed locally; independent CI pending |
| R2-R04 | `test_journal_integrity.py::test_torn_tail_recovered_complete_records_preserved` | Initial regression passed locally; independent CI pending |
| R3-R04 | `test_journal_integrity.py::test_step_commit_failure_is_atomic` | Initial regression passed locally; independent CI pending |
| W1 | No test ID | OPEN |
| F7/F8 | No restored depth-7 proof | OPEN |
| F10/F11 | No complete responder construction test | OPEN |
| Ratchet | No preregistered experiment | NOT TESTED |

A claim must not be labelled **Established** unless its table entry names an executable test ID included in required CI and a passing CI run for the exact commit. CI support is not a proof of universal behavior. Model review comments remain advisory.

## Change-control rule

Any change to physics or evidence must name the claims potentially invalidated, attach before/after failing tests, and preserve outdated claims in an amendment rather than silently rewriting historical results. Store review notes in `docs/reviews/` with paths, reproduction steps, and a clear status.

## Primary next hypothesis

Can independent agents inherit *working physical configurations* that expand a fresh entrant's reachable capability frontier under matched computation, labor, materials and locally available usable energy? Do not confuse inherited design text with inherited functioning apparatus.
