from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .schemas import MergedMonster, RejectedRecord, RunManifest


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS ingestion_runs (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    collected_count INTEGER NOT NULL CHECK (collected_count >= 0),
    accepted_count INTEGER NOT NULL CHECK (accepted_count >= 0),
    rejected_count INTEGER NOT NULL CHECK (rejected_count >= 0),
    merged_count INTEGER NOT NULL CHECK (merged_count >= 0),
    conflict_count INTEGER NOT NULL CHECK (conflict_count >= 0),
    manifest_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS monsters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stable_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL COLLATE NOCASE UNIQUE,
    armor INTEGER NOT NULL CHECK (armor >= 0),
    HP INTEGER NOT NULL CHECK (HP > 0),
    challenge_rating REAL,
    challenge_rating_raw TEXT,
    strength INTEGER NOT NULL,
    dexterity INTEGER NOT NULL,
    constitution INTEGER NOT NULL,
    intelligence INTEGER NOT NULL,
    wisdom INTEGER NOT NULL,
    charisma INTEGER NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    gold_loot_min INTEGER NOT NULL DEFAULT 0 CHECK (gold_loot_min >= 0),
    gold_loot_max INTEGER NOT NULL DEFAULT 0 CHECK (gold_loot_max >= gold_loot_min),
    items_loot TEXT NOT NULL DEFAULT '[]',
    ingestion_run_id TEXT NOT NULL REFERENCES ingestion_runs(id)
);

CREATE TABLE IF NOT EXISTS monster_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    monster_id INTEGER NOT NULL REFERENCES monsters(id) ON DELETE CASCADE,
    ingestion_run_id TEXT NOT NULL REFERENCES ingestion_runs(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    source_url TEXT,
    collected_at TEXT NOT NULL,
    selected INTEGER NOT NULL CHECK (selected IN (0, 1)),
    UNIQUE (ingestion_run_id, source, source_record_id)
);

CREATE TABLE IF NOT EXISTS rejected_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingestion_run_id TEXT NOT NULL REFERENCES ingestion_runs(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    message TEXT NOT NULL,
    payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_monsters_name ON monsters(name COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_monsters_challenge_rating ON monsters(challenge_rating);
CREATE INDEX IF NOT EXISTS idx_monster_sources_lookup
    ON monster_sources(source, source_record_id);
CREATE INDEX IF NOT EXISTS idx_monster_sources_monster ON monster_sources(monster_id);
"""


def create_schema(connection: sqlite3.Connection) -> None:
    existing_columns = {
        row[1] for row in connection.execute("PRAGMA table_info(monsters)").fetchall()
    }
    if existing_columns and "stable_key" not in existing_columns:
        connection.execute("DROP TABLE monsters")
    connection.executescript(SCHEMA_SQL)


def replace_dataset(
    db_path: Path,
    manifest: RunManifest,
    monsters: list[MergedMonster],
    rejected: list[RejectedRecord],
) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    try:
        create_schema(connection)
        with connection:
            connection.execute("DELETE FROM monster_sources")
            connection.execute("DELETE FROM monsters")
            connection.execute(
                """INSERT INTO ingestion_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    manifest.run_id,
                    manifest.started_at.isoformat(),
                    manifest.completed_at.isoformat(),
                    manifest.collected,
                    manifest.accepted_source_records,
                    manifest.rejected,
                    manifest.merged,
                    manifest.conflicts,
                    manifest.model_dump_json(),
                ),
            )
            for merged in monsters:
                monster = merged.monster
                cursor = connection.execute(
                    """INSERT INTO monsters (
                        stable_key, name, armor, HP, challenge_rating,
                        challenge_rating_raw, strength, dexterity, constitution,
                        intelligence, wisdom, charisma, description, gold_loot_min,
                        gold_loot_max, items_loot, ingestion_run_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        monster.stable_key,
                        monster.name,
                        monster.armor,
                        monster.hp,
                        float(monster.challenge_rating) if monster.challenge_rating is not None else None,
                        monster.challenge_rating_raw,
                        monster.strength,
                        monster.dexterity,
                        monster.constitution,
                        monster.intelligence,
                        monster.wisdom,
                        monster.charisma,
                        monster.description,
                        monster.gold_loot_min,
                        monster.gold_loot_max,
                        json.dumps(monster.items_loot, ensure_ascii=False),
                        manifest.run_id,
                    ),
                )
                monster_id = cursor.lastrowid
                for source in merged.sources:
                    connection.execute(
                        """INSERT INTO monster_sources (
                            monster_id, ingestion_run_id, source, source_record_id,
                            source_url, collected_at, selected
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            monster_id,
                            manifest.run_id,
                            source.source.value,
                            source.source_record_id,
                            source.source_url,
                            source.collected_at.isoformat(),
                            int(source.selected),
                        ),
                    )
            for record in rejected:
                connection.execute(
                    """INSERT INTO rejected_records (
                        ingestion_run_id, source, source_record_id, reason_code,
                        message, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        manifest.run_id,
                        record.source.value,
                        record.source_record_id,
                        record.reason_code,
                        record.message,
                        json.dumps(record.payload, ensure_ascii=False),
                    ),
                )
    finally:
        connection.close()
