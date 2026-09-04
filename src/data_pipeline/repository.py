from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ALLOWED_ORDERING = {
    "name": "m.name COLLATE NOCASE",
    "challenge_rating": "m.challenge_rating",
    "hp": "m.HP",
    "armor": "m.armor",
}


@dataclass(frozen=True)
class MonsterPage:
    items: list[dict[str, Any]]
    total: int


class DatasetRepository:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def list_monsters(
        self,
        *,
        search: str | None = None,
        challenge_min: float | None = None,
        challenge_max: float | None = None,
        ordering: str = "name",
        limit: int = 20,
        offset: int = 0,
    ) -> MonsterPage:
        descending = ordering.startswith("-")
        ordering_key = ordering.removeprefix("-")
        order_column = ALLOWED_ORDERING.get(ordering_key)
        if order_column is None:
            raise ValueError(f"unsupported ordering: {ordering}")

        conditions = []
        parameters: list[Any] = []
        if search:
            conditions.append("m.name LIKE ? ESCAPE '\\' COLLATE NOCASE")
            escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            parameters.append(f"%{escaped}%")
        if challenge_min is not None:
            conditions.append("m.challenge_rating >= ?")
            parameters.append(challenge_min)
        if challenge_max is not None:
            conditions.append("m.challenge_rating <= ?")
            parameters.append(challenge_max)
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        direction = "DESC" if descending else "ASC"

        connection = self._connect()
        try:
            total = connection.execute(
                f"SELECT COUNT(*) FROM monsters m {where}", parameters
            ).fetchone()[0]
            rows = connection.execute(
                f"""SELECT m.id, m.stable_key, m.name, m.armor, m.HP AS hp,
                           m.challenge_rating, m.challenge_rating_raw,
                           m.strength, m.dexterity, m.constitution,
                           m.intelligence, m.wisdom, m.charisma, m.description
                    FROM monsters m
                    {where}
                    ORDER BY {order_column} {direction}, m.id ASC
                    LIMIT ? OFFSET ?""",
                [*parameters, limit, offset],
            ).fetchall()
            return MonsterPage([dict(row) for row in rows], total)
        finally:
            connection.close()

    def get_monster(self, monster_id: int) -> dict[str, Any] | None:
        connection = self._connect()
        try:
            row = connection.execute(
                """SELECT m.id, m.stable_key, m.name, m.armor, m.HP AS hp,
                          m.challenge_rating, m.challenge_rating_raw,
                          m.strength, m.dexterity, m.constitution,
                          m.intelligence, m.wisdom, m.charisma, m.description,
                          m.gold_loot_min, m.gold_loot_max, m.items_loot,
                          m.ingestion_run_id
                   FROM monsters m WHERE m.id = ?""",
                (monster_id,),
            ).fetchone()
            if row is None:
                return None
            result = dict(row)
            result["sources"] = [
                dict(source)
                for source in connection.execute(
                    """SELECT source, source_record_id, source_url, collected_at, selected
                       FROM monster_sources WHERE monster_id = ? ORDER BY source""",
                    (monster_id,),
                ).fetchall()
            ]
            return result
        finally:
            connection.close()

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        connection = self._connect()
        try:
            row = connection.execute(
                """SELECT id, started_at, completed_at, collected_count,
                          accepted_count, rejected_count, merged_count, conflict_count
                   FROM ingestion_runs WHERE id = ?""",
                (run_id,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            connection.close()
