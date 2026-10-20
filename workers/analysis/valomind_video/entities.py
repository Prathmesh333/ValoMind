"""Conservative entity proposals. Co-occurrence is never a player-agent assignment."""

import re
import unicodedata

KINDS = {"player", "team", "map", "character_agent"}


def normalize(value):
    return " ".join(re.findall(r"\w+", unicodedata.normalize("NFKC", value).casefold()))


def validate_catalog(catalog):
    if not isinstance(catalog, list):
        raise TypeError("Catalog must be a list")
    seen = set()
    for entry in catalog:
        if set(entry) != {"kind", "id", "aliases"} or entry["kind"] not in KINDS:
            raise ValueError("Catalog entries require kind, id and aliases")
        if not isinstance(entry["id"], str) or not entry["id"].strip():
            raise ValueError("Entity ID must be a nonempty string")
        if (entry["kind"], entry["id"]) in seen:
            raise ValueError("Duplicate entity ID")
        seen.add((entry["kind"], entry["id"]))
        if not isinstance(entry["aliases"], list) or not entry["aliases"]:
            raise ValueError("Aliases must be a nonempty list")
        if any(not isinstance(alias, str) or not normalize(alias) for alias in entry["aliases"]):
            raise ValueError("Aliases must contain readable text")
    return catalog


def resolve(proposals, catalog):
    """Match complete OCR strings or explicit detector labels; reject ambiguous aliases."""
    index = {}
    for entry in validate_catalog(catalog):
        for alias in entry["aliases"]:
            index.setdefault(normalize(alias), set()).add((entry["kind"], entry["id"]))
    result = []
    for proposal in proposals:
        text = proposal.get("text", "") if proposal["kind"] == "ocr" else proposal["label"]
        matches = index.get(normalize(text), set())
        if len(matches) != 1:
            continue
        kind, identity = next(iter(matches))
        entity = dict(proposal, kind=f"entity.{kind}", label=identity)
        entity[
            {
                "player": "player_id",
                "team": "team_id",
                "map": "map_id",
                "character_agent": "character_agent_id",
            }[kind]
        ] = identity
        result.append(entity)
    return result
