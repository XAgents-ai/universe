# Threat-model shared participant state and journaling

Identify and reproduce information/authority leaks across independent entrants through the viewer, observation budget, actor API, owner claim, event journal and restart replay. Record whether exposure comes from prior training, current global observer access or local paid sensing.

Acceptance: adversarial HTTP tests; rejection of unauthorized operations; no global observation in actor responses; token confidentiality in logged/outgoing data; deterministic recovery; documented deployment limits. Do not expose the prototype on the public Internet.


**J1 — Unverified participant identity (OPEN):** The bearer token authenticates an issued session only; it does not prove a physical human, unique person, distinct model provider, or independent cognition. Establish the testable threat model for Sybil identities and token delegation; expose the distinction between actor label, authenticated session, and verified provenance. The system must not make claims of independent human/model participation without separate identity evidence. Preserve viewer anonymity and do not collect invasive identity data as a default.
