> **Security/evidence hardening update (2026-10-17):** This repository adds token-digest journaling, staged journal-first commits and torn-tail recovery tests. AI reviews are manually triggered, advisory and run from the trusted default branch; action source pinning and active branch protection are required before connecting model API secrets. World-owned batched clock and restored depth-seven oracle negative remain OPEN. See `docs/ROADMAP.md` and `docs/GITHUB_SETUP.md`.

> **Shared development setup (2026-10-17):** This is the R0.3 scientific baseline, now equipped with independent Codex/Claude workflows. See [`docs/GITHUB_SETUP.md`](docs/GITHUB_SETUP.md) to publish to a private repository you own, [`docs/COLLABORATION.md`](docs/COLLABORATION.md) for review rules, [`docs/SCIENTIFIC_CLAIMS.md`](docs/SCIENTIFIC_CLAIMS.md) for established versus open claims, and [`AGENTS.md`](AGENTS.md) / [`CLAUDE.md`](CLAUDE.md) for model instructions. AI integrations are **not authenticated or running** until you configure your accounts and GitHub secrets.

# Universe V0 R0.3 — Physical World & Shared-Agent Prototype

*A digital universe whose viewer shows state, not stories. Its inhabitants have one charged physical interface; experimental interventions belong to isolated clones.*

## What runs today

The actual Python physical kernel simulates a discrete 2D lattice with 9 primitive species (S/C/G/A/W/B/P/K/R), stored and excited energy, bonds, heat transport and dissipation, seeded conflicts, fixed-point/integer energy accounting, deterministic replays, and localized world-owned energy inputs.

- **Physical construction proved:** `v0_responder.py` finds a charged-control-only witness assembling a bonded P→A autonomous sensor–actuator from two loose pieces using pre-existing, ordinary construction arms. The constructed mechanism responds *after* its external controller stops. The agent never invokes `create_machine`; no script is installed in the constructed device.
- **Existing retained state:** `v0_memory_witness.py` demonstrates a separately hand-placed 1-bit circulating-pulse memory, with write/hold/read/erase; this remains O1 only, not a construction witness.
- **Oracle:** `v0_oracle.py` finds a C–A construction; `v0_responder.py` finds a P–A responder. `Params.cold()` uses an explicitly **canonical conflict policy** for bounded search, whereas live physics retains the original seeded conflict policy. They are distinct dynamics; exhaustion in canonical cold mode cannot prove impossibility in live stochastic mode.
- **Shared persistent universe:** `open_world.py` lets up to four independent entrants (human, model, program controllers) join the **same** world using pre-placed ordinary entry actuators. Their charged local action API is identical. A JSONL journal records actions and verifies world hashes when replayed after restart.
- **Viewer:** audit replay of the actual P–A construction and stimulus, global read-only live observer, shared human agent, separate solo sandbox agent, and isolated experimental clone. Particles/bonds/quanta/heat are rendered as material state, not named machines. A participant sees only previously paid local observations, not the viewer's global state.

This is **not** an artificial-life result, a general-purpose game, a 3D world, or an empirical demonstration of open-ended cumulative inheritance. An externally supplied AI model has not yet been connected; the HTTP interface permits one to connect. This code is a local research prototype, **not a hardened public multi-user server**.

## Setup and run

Python 3.10+ recommended.

```bash
python -m pip install -r requirements.txt
python -m uvicorn server:app --host 127.0.0.1 --port 8765
```

Open **http://127.0.0.1:8765** in a browser.

| Tab | Access | Effect |
|---|---|---|
| Witness replay | Full recorded state, ledger and timeline | None |
| Live observer | Full current shared-world state | None |
| Join universe | Charged `observe`, `set`, `claim` and `wait` | Only through owned control sites |
| Solo sandbox | Same limited physical interface in isolated world | Isolated from the open universe |
| Experiment | Full global state in isolated clone | Logged `drop`, `remove`, `replace` only |

The **live universe is persistent across server restarts**. State is stored in `.universe_state/events.jsonl` by default (or set `UNIVERSE_STATE_DIR`). The browser tries to preserve its private participant token in tab/session storage so refreshing does not consume an entry slot. A server-side ledger replays every event and verifies its chain and physical state hash on startup. Four entrants max because only four physical seed actuators were placed initially. Time advances only on participant actions, not by a wall-clock timer.

You can audit the durable journal after running the server:

```bash
python verify_journal.py .universe_state
```

## Let an independent program enter

With the server running:

```bash
python example_agent_client.py --steps 8
```

This joins as a **program** and executes an intentionally simple deterministic reference policy. It prints a private resume token, and future runs can pass `--token <TOKEN>` to continue as the same entrant. The script does **not** claim to be an LLM. To connect Claude, Gemini, or another model, adapt `choose_action(view)` to call that model, pass it **only** the actor-view response, and send its chosen `set`/`observe`/`claim`/`wait` request to the same API. No text message or agent-authored code is inserted into the simulated world.

REST summary (local only):

```text
POST /api/live/join                {"controller":"model", "global_exposure_declared":false}
GET  /api/live/actor              Authorization: Bearer <token>
POST /api/live/act                Authorization: Bearer <token>
                                  {"kind":"observe"|"set"|"claim"|"wait", "x":3,"y":4}
GET  /api/live/observer           global state, no write
GET  /api/live/events             global audit journal with bearer tokens removed
```

Access to global observer data is legitimate but must be separately reported if an agent is later evaluated as a supposedly locally informed participant. Controller type and declared current-instance global exposure are recorded; model pretraining exposure needs additional experiment metadata before publication.

## Run the evidence checks

```bash
bash run_checks.sh
# Optional browser automation: requires Playwright and a local Chromium executable at /usr/bin/chromium
WITH_BROWSER=1 bash run_checks.sh
```

The positive experiments include:

- Core deterministic replay, energy/matter ledger fuzz, four counterfactual clones, memory witness.
- F1–F5 regressions, F6 regression distinguishing canonical-cold vs seeded-live conflicts.
- Two O2 construction witnesses; P–A responder built from loose P/A with three charged writes, four post-disconnect contrasts, 12/12 replay seeds.
- Small canonical-cold bounded negative: horizon four, eight generated successor attempts. **Do not reuse R0.2's unrevalidated depth-7 stochastic exhaustion claim.**
- Live shared-world actors, cross-actor authorization, live/observer API boundaries, journal restart replay.
- Optional headless Chromium checks of the viewer and live tabs.

The canonical cold oracle uses `max_nodes` to bound successor *generation*; those counts are not unique states. `physical_key()` is a state equivalence only for the stated search model. Production seeded dynamics remain stochastic with fixed-seed replay and cannot be fully represented by the same cold-state equivalence.

## Constraints and known weaknesses

1. No complete P→C→G→C→A seeded construction witness yet; only the smaller P→A autonomous structure is physically assembled. The fuller circuit is hand-placed in an older O1 check.
2. Human/model open participation is supported by identical **physical APIs**, but no external LLM is running in the demo by default. There is no proof of emergent life, cognition, self-reproduction, or capability accumulation across agents.
3. The open world's four seed actuators and loose initial materials are initial conditions. No raw-matter bootstrap of actuators is claimed. Entry authorization is assigned at admission; no matter is created in the live universe on join.
4. No dynamic new agent entry after four seed slots are assigned. No sleep/wall-clock evolution, object movement for bonded clusters, heat engine, gravity, momentum, or spontaneous species production.
5. HTTP authorization tokens and full journal are held on a local machine; there is no rate limiting, public identity, remote permissions policy, TLS termination, secure secret manager, state database transaction, or anti-tamper signatures. Do **not** expose `--host 0.0.0.0` to the public Internet.
6. Human global observer access is not prohibited. A participant who used it is a distinct experimental condition; self-declared provenance alone is not sufficient for blinded science.
7. The A–D factorial, procedural family generator, native physics ablations, and intergenerational `R(W,B)` ratchet have not been implemented or experimentally demonstrated. They remain research objectives.

## Review materials

- `UNIVERSE_V0_PHYSICS_SPEC.md` — R0.3 normative specification and defined evidence limits.
- `UNIVERSE_V0_PHYSICS_SPEC_R0_2.md` — unmodified archived predecessor.
- `CLAUDE_REVIEW_REQUEST.md` — explicit adversarial review contract and key falsifiers.
- `RUN_RESULTS.txt` — captured actual test output from this build.
- `v0_kernel.py`, `open_world.py`, `v0_responder.py` — implementation under review.
- `o2_witness_autonomous_responder.json` — the physical construction witness.
- `preview.png`, `preview_live_observer.png`, `preview_live_agent.png` — screenshot evidence, not substitute for replay.

## Provenance principle

A statement such as “an agent built a machine” is a **claim** until an event trace demonstrates legal material transitions, energy accounting, reproducible functionality, and the absence of privileged construction commands. This viewer is meant to help inspect those claims—not decorate them.

**Archived counterexample:** `test_f6_original_counterexample_r02.py` intentionally reproduces the old F6 failure when run against `v0_kernel_r02.py` and returns a nonzero exit status. It is kept for scientific provenance and excluded from the current acceptance suite. R0.3's passing comparison is `test_f6_resolution.py`.

### Governance G2 update (2026-10-17)

The repository includes Claude's H1 governance patch, a write-token checkout correction, protected-path tests, and immutable-action preflights. The physics remains R0.3. See `docs/reviews/CLAUDE_GOVERNANCE_G2_RESPONSE.md` and `docs/GITHUB_SETUP.md`. **All model actions are blocked pending verified SHA pins; Codex publication is also held pending separation into a trusted publish job.** You can safely bootstrap a private repository and run secret-free CI without enabling model credentials.

Licensed under MIT; see `LICENSE`.
