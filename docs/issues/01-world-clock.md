# W1 — World-owned clock and batched participant actions

**Owner/reviewer acceptance criteria — preregistered.** Currently each API request advances world time; request arrival order can determine outcomes. Define a world-owned tick barrier that collects at most one action per participant, permits deterministic no-op on missing action, and advances on a declared scheduler independent of which participant called first. Include seeded tie-break or canonical ordering, timeout policy, logged batch and replay hashes. Compare two permutations of identical action submissions; their resulting tick states must be equivalent (or deliberately distinguished by a pre-registered conflict rule). Human and model controllers use identical clocks. Preserve charged controls and forbidden boundary ops. Do NOT grant clients a privileged `tick` or `admin_edit` endpoint in public universe.

Status: OPEN — do not treat current HTTP call-to-tick behavior as world-owned clock.
