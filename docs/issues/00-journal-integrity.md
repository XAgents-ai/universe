# T2 / R2 / R3 — Journal privacy, atomic commit, torn-tail recovery

**Owner/reviewer acceptance criteria — frozen before implementation.** A journal must never persist raw bearer tokens; joined participants must still be authenticated across process restart. State transitions must be staged on a clone and made live only after a durable journal append. A partial trailing record must be truncated; a corrupted complete record must abort recovery. Any fsync failure must prevent subsequent writes until replay. Tests: `test_journal_integrity.py` and `test_live_world.py`, both required in `run_checks.sh`. Never claim crash-safe transactional durability on all filesystems without power-loss testing.

Implementation status: local collaboration package includes an initial patch and tests. Independent review still required.
