from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SourceName(StrEnum):
    SCRAPED = "scraped_monsters"
    CURATED = "curated_monsters"


class RawMonster(BaseModel):
    model_config = ConfigDict(extra="allow")

    source: SourceName
    source_record_id: str
    source_url: str | None = None
    collected_at: datetime
    payload: dict[str, Any]


class CanonicalMonster(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stable_key: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    name: str = Field(min_length=1, max_length=200)
    armor: int = Field(ge=0, le=100)
    hp: int = Field(gt=0, le=100_000)
    challenge_rating: Decimal | None = Field(default=None, ge=0, le=100)
    challenge_rating_raw: str | None = None
    strength: int = Field(ge=-20, le=20)
    dexterity: int = Field(ge=-20, le=20)
    constitution: int = Field(ge=-20, le=20)
    intelligence: int = Field(ge=-20, le=20)
    wisdom: int = Field(ge=-20, le=20)
    charisma: int = Field(ge=-20, le=20)
    description: str = ""
    gold_loot_min: int = Field(default=0, ge=0)
    gold_loot_max: int = Field(default=0, ge=0)
    items_loot: list[str] = Field(default_factory=list)

    @field_validator("name", "description")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("items_loot")
    @classmethod
    def clean_items(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value and value.strip()]


class RejectedRecord(BaseModel):
    source: SourceName
    source_record_id: str
    reason_code: str
    message: str
    payload: dict[str, Any]


class SourceReference(BaseModel):
    source: SourceName
    source_record_id: str
    source_url: str | None
    collected_at: datetime
    selected: bool


class MergedMonster(BaseModel):
    monster: CanonicalMonster
    sources: list[SourceReference]


class RunManifest(BaseModel):
    run_id: str
    started_at: datetime
    completed_at: datetime
    source_counts: dict[str, int]
    collected: int
    accepted_source_records: int
    rejected: int
    merged: int
    conflicts: int
    output_files: dict[str, str]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
