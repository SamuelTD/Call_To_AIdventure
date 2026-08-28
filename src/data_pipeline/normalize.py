from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from typing import Any

from pydantic import ValidationError

from .schemas import CanonicalMonster, RawMonster, RejectedRecord


REQUIRED_FIELDS = ("name", "armor", "HP")
ABILITY_FIELDS = (
    "strength",
    "dexterity",
    "constitution",
    "intelligence",
    "wisdom",
    "charisma",
)


def stable_key(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_name.casefold()).strip("-")


def parse_integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{field} must be an integer")
    match = re.search(r"[+-]?\d+", str(value).strip())
    if not match:
        raise ValueError(f"{field} must contain an integer")
    return int(match.group())


def parse_challenge_rating(value: Any) -> tuple[Decimal | None, str | None]:
    if value is None:
        return None, None
    raw = str(value).strip()
    if not raw or raw.casefold() in {"none", "n/a", "unknown", "-"}:
        return None, raw or None
    try:
        if "/" in raw:
            fraction = Fraction(raw)
            return Decimal(fraction.numerator) / Decimal(fraction.denominator), raw
        return Decimal(raw), raw
    except (InvalidOperation, ValueError, ZeroDivisionError) as exc:
        raise ValueError("challenge_rating is not a number or fraction") from exc


def normalize(raw: RawMonster) -> CanonicalMonster:
    payload = raw.payload
    missing = [field for field in REQUIRED_FIELDS if payload.get(field) in (None, "")]
    if missing:
        raise ValueError(f"missing mandatory fields: {', '.join(missing)}")

    name = str(payload["name"]).strip()
    challenge_rating, challenge_rating_raw = parse_challenge_rating(
        payload.get("challenge_rating")
    )
    gold = payload.get("gold_loot") or [0, 0]
    if not isinstance(gold, (list, tuple)) or len(gold) != 2:
        raise ValueError("gold_loot must contain a minimum and maximum")
    gold_min = parse_integer(gold[0], "gold_loot_min")
    gold_max = parse_integer(gold[1], "gold_loot_max")
    if gold_min > gold_max:
        raise ValueError("gold_loot minimum cannot exceed maximum")

    values = {
        field: parse_integer(payload.get(field, 0), field) for field in ABILITY_FIELDS
    }
    return CanonicalMonster(
        stable_key=stable_key(name),
        name=name,
        armor=parse_integer(payload["armor"], "armor"),
        hp=parse_integer(payload["HP"], "HP"),
        challenge_rating=challenge_rating,
        challenge_rating_raw=challenge_rating_raw,
        description=str(payload.get("description") or "").strip(),
        gold_loot_min=gold_min,
        gold_loot_max=gold_max,
        items_loot=payload.get("items_loot") or [],
        **values,
    )


def normalize_or_reject(
    raw: RawMonster,
) -> tuple[CanonicalMonster | None, RejectedRecord | None]:
    try:
        return normalize(raw), None
    except (ValueError, TypeError, ValidationError) as exc:
        return None, RejectedRecord(
            source=raw.source,
            source_record_id=raw.source_record_id,
            reason_code="VALIDATION_ERROR",
            message=str(exc),
            payload=raw.payload,
        )
