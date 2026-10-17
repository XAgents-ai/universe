# R0.2 oracle review: F5 closed; F6 open

**F5:** periodic-source phase is now part of `physical_key`, correctly distinguishing equal configurations at different source phases. The archived R0.1 key did not.

**F6:** with `Params.cold()` the engine still calls `rng.shuffle(props)` to resolve same-tick conflicts (kernel phase 5). Its state and entropy consumption are omitted from the cold search key, as are heat states that can affect later RNG consumption. Two seeded worlds containing exactly two excited C conductors pointing into a third C have identical `physical_key` values but different winners after one tick. See `test_f6_rng_key.py` (fails on R0.2 by design).

**Scientific implication:** Positive witness traces are direct replayable evidence, unaffected by search-state pruning. The negative claim `NOT_ESTABLISHED / exhausted` must be qualified: the visited-state equivalence can prune dynamically distinct states. A negative result remains valid only within the particular quotient search actually explored, not as a complete depth-bounded cold-physics reachability statement.

**Possible repairs (not implemented):**
1. Conservative search key: include cold-mode RNG state and heat distribution, and all other states affecting future transitions; expect much weaker deduplication.
2. Define a separate deterministic **cold oracle semantics** with canonical, non-random conflict priorities and prove omitted state fields cannot affect its projected dynamics. Mark this explicitly as a different search model; replay all witnesses under actual R0.2 dynamics and do not claim real stochastic reachability completeness.
3. Explore all physically possible tie-break results as branches and use an equivalence proof for state reduction; more expensive but a stronger nondeterministic reachability claim.

**Participation metadata caution:** prior human/LLM engineering knowledge is not equivalent to an actual view of the current world's hidden global state. Register baseline prior and current-state observation channels separately (e.g., `controller_type`, `live_observation_access`, `world_prior_exposure`). Information attribution, not gameplay fairness, is the goal.
