# Local broadcast index

This increment implements a metadata contract and offline CLI. It accepts reviewed
roster observations, keeping a player's agent pick attached to a specific map game.
One video can contain multiple series/map games; the same player can change agents
between map games. Missing picks stay unknown and partial rosters remain partial.

Run the synthetic example from the repository root:

```powershell
uv run python scripts/index_broadcast.py packages/contracts/fixtures/broadcast.json
```

The result contains player/team records and evidence-linked pick observations.
The fixture shows one invented player on Jett in one map game and Cypher in another.
It is intentionally incomplete and must not be interpreted as a ten-player roster.
Redirect stdout to a JSON file to keep the index. Invalid manifests exit with code 2.

Every pick includes a source-relative evidence range, extraction method, confidence,
author and review status. Independent review is required for inclusion in the index.
Confidence alone never verifies a detection. Source URLs are metadata only: the CLI
does not fetch, download, decode or train on footage. Source permission status is
retained, and synthetic/unconfirmed/revoked sources are not training eligible.
The eligibility flag only concerns source metadata; it is not a training dataset
quality certification or permission verification service.

Requirements: M0 shared fixtures/contracts; preparatory M1 provenance and review;
PRD-03 and docs/05. Input boundary: local JSON only, no API endpoint or private media.
No migration is added. This is an offline index export, not a persistent multi-user
database. Reviewer IDs are declarations in a local manifest; authenticated reviewer
identity and immutable review history require the M1 service.

Tests cover cross-map agent changes, proposal exclusion, independent review,
unresolved identities, duplicate picks, evidence bounds, unknown fields and source
eligibility. Next steps are the annotation/review service, local video probing,
frame sampling and HUD crop proposals. OCR/YOLO integration follows a labeled
benchmark; no model training or automated video extraction is implemented yet.
