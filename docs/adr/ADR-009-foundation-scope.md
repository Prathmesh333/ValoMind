# ADR-009: Start implementation at the workspace root

Accepted 2026-10-20. The workspace held specifications only, with no Git repository
or existing application. Keep the supplied documents intact and implement the
suggested layout at the workspace root. Follow their engineering instructions for
the implementation as well.

Deliver M0 in small tested increments. The first is the API/schema foundation.
No frontend, ingestion or training completion is implied by directory scaffolds.
Use a separate configured token for synthetic fixture access until M1 workspace
authentication exists. The fixture route never reads private gameplay records.

Requirements: M0; PRD-10; synthetic labeling portion of S-09. Boundaries: public
health probes, token-protected invented fixture, database migration administration.
No footage, third-party identity, Riot credential or external provider is required.
Coverage: five invented rounds, no observed events or training labels. Tests cover
fixture flags, bearer access, error format and liveness; CI checks migration reversal.
