import json
from copy import deepcopy
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import ValidationError
from valomind.broadcast import BroadcastManifest, build_index

FIXTURE = Path(__file__).resolve().parents[3] / "packages/contracts/fixtures/broadcast.json"


@pytest.fixture
def raw():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_player_can_change_agent_between_map_games(raw):
    index = build_index(BroadcastManifest.model_validate(raw))
    assert [row["character_agent_id"] for row in index["observations"]] == ["jett", "cypher"]
    assert len({row["player_id"] for row in index["observations"]}) == 1
    assert index["eligible_for_training"] is False
    assert index["is_synthetic"] is True


def test_model_confidence_does_not_verify_a_pick(raw):
    evidence = raw["map_games"][0]["picks"][0]["evidence"]
    evidence.update(method="detector", status="proposed", confidence=1.0, reviewer_id=None)
    index = build_index(BroadcastManifest.model_validate(raw))
    assert len(index["observations"]) == 1
    assert index["pending_review"] == 1


@pytest.mark.parametrize("mutation", ["self_review", "unknown_player", "outside_game", "duplicate"])
def test_bad_attribution_rejected(raw, mutation):
    game = raw["map_games"][0]
    pick = game["picks"][0]
    if mutation == "self_review":
        pick["evidence"]["reviewer_id"] = pick["evidence"]["author_id"]
    elif mutation == "unknown_player":
        pick["player_id"] = str(UUID(int=999))
    elif mutation == "outside_game":
        pick["evidence"]["end_ms"] = game["end_ms"] + 1
    else:
        game["picks"].append(deepcopy(pick))
    with pytest.raises(ValidationError):
        BroadcastManifest.model_validate(raw)


def test_unknown_agent_remains_null(raw):
    raw["map_games"][0]["picks"][0]["character_agent_id"] = None
    index = build_index(BroadcastManifest.model_validate(raw))
    assert index["observations"][0]["character_agent_id"] is None


def test_unconfirmed_real_source_is_not_training_eligible(raw):
    raw["is_synthetic"] = False
    assert not build_index(BroadcastManifest.model_validate(raw))["eligible_for_training"]


def test_confirmation_requires_reference(raw):
    raw["footage_use_status"] = "confirmed"
    with pytest.raises(ValidationError):
        BroadcastManifest.model_validate(raw)


def test_overlapping_games_rejected(raw):
    raw["map_games"][1]["start_ms"] = 59000
    with pytest.raises(ValidationError):
        BroadcastManifest.model_validate(raw)
