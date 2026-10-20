"""Offline broadcast indexing contracts. Detector output is a proposal, never fact."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Evidence(Record):
    start_ms: int = Field(ge=0)
    end_ms: int = Field(gt=0)
    method: Literal["manual", "ocr", "portrait_match", "detector"]
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)
    status: Literal["proposed", "reviewed", "rejected"] = "proposed"
    author_id: UUID
    reviewer_id: UUID | None = None

    @model_validator(mode="after")
    def valid_review(self):
        if self.end_ms <= self.start_ms:
            raise ValueError("Evidence end must follow start")
        if self.status == "reviewed" and (
            self.reviewer_id is None or self.reviewer_id == self.author_id
        ):
            raise ValueError("Reviewed evidence requires an independent reviewer")
        return self


class Player(Record):
    id: UUID
    display_name: str = Field(min_length=1)


class Team(Record):
    id: UUID
    display_name: str = Field(min_length=1)


class Pick(Record):
    player_id: UUID
    team_id: UUID
    character_agent_id: str | None = Field(default=None, min_length=1)
    evidence: Evidence


class MapGame(Record):
    id: UUID
    series_id: UUID
    map_id: str | None = Field(default=None, min_length=1)
    team_ids: list[UUID] = Field(min_length=2, max_length=2)
    start_ms: int = Field(ge=0)
    end_ms: int = Field(gt=0)
    picks: list[Pick] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def valid_game(self):
        if self.end_ms <= self.start_ms or len(set(self.team_ids)) != 2:
            raise ValueError("Map game requires a valid interval and two distinct teams")
        seen = set()
        counts = dict.fromkeys(self.team_ids, 0)
        for pick in self.picks:
            if pick.player_id in seen:
                raise ValueError("A player may have only one pick per map game")
            seen.add(pick.player_id)
            if pick.team_id not in counts:
                raise ValueError("Pick references a team outside this map game")
            counts[pick.team_id] += 1
            if counts[pick.team_id] > 5:
                raise ValueError("A team may have at most five players per map game")
            if not self.start_ms <= pick.evidence.start_ms < pick.evidence.end_ms <= self.end_ms:
                raise ValueError("Pick evidence must lie inside its map game")
        return self


class BroadcastManifest(Record):
    schema_version: Literal["broadcast_v1"] = "broadcast_v1"
    source_id: UUID
    source_url: str = Field(min_length=1)
    source_channel: str = Field(min_length=1)
    duration_ms: int = Field(gt=0)
    is_synthetic: bool
    footage_use_status: Literal["unconfirmed", "confirmed", "revoked"] = "unconfirmed"
    rights_reference: str | None = Field(default=None, min_length=1)
    players: list[Player]
    teams: list[Team]
    map_games: list[MapGame]

    @model_validator(mode="after")
    def valid_manifest(self):
        if self.footage_use_status == "confirmed" and not self.rights_reference:
            raise ValueError("Confirmed footage use requires a rights reference")
        for records in (self.players, self.teams, self.map_games):
            if len({record.id for record in records}) != len(records):
                raise ValueError("Duplicate record IDs")
        players = {p.id for p in self.players}
        teams = {t.id for t in self.teams}
        previous_end = 0
        for game in sorted(self.map_games, key=lambda game: game.start_ms):
            if game.start_ms < previous_end or game.end_ms > self.duration_ms:
                raise ValueError("Map game intervals overlap or exceed source duration")
            previous_end = game.end_ms
            if not set(game.team_ids) <= teams:
                raise ValueError("Unknown team reference")
            if any(p.player_id not in players for p in game.picks):
                raise ValueError("Unknown player reference")
        return self


def build_index(manifest: BroadcastManifest) -> dict:
    """Index reviewed observations, preserving map-game context and incomplete coverage."""
    observations = []
    pending = 0
    for game in manifest.map_games:
        for pick in game.picks:
            if pick.evidence.status != "reviewed":
                pending += pick.evidence.status == "proposed"
                continue
            observations.append(
                {
                    "source_id": str(manifest.source_id),
                    "source_url": manifest.source_url,
                    "series_id": str(game.series_id),
                    "map_game_id": str(game.id),
                    "map_id": game.map_id,
                    "player_id": str(pick.player_id),
                    "team_id": str(pick.team_id),
                    "character_agent_id": pick.character_agent_id,
                    "evidence": pick.evidence.model_dump(mode="json"),
                }
            )
    return {
        "schema_version": "broadcast_index_v1",
        "is_synthetic": manifest.is_synthetic,
        "footage_use_status": manifest.footage_use_status,
        "eligible_for_training": (
            not manifest.is_synthetic and manifest.footage_use_status == "confirmed"
        ),
        "coverage": "Observed picks only; not a complete roster or pick-frequency dataset.",
        "pending_review": pending,
        "players": [p.model_dump(mode="json") for p in manifest.players],
        "teams": [t.model_dump(mode="json") for t in manifest.teams],
        "observations": observations,
    }
