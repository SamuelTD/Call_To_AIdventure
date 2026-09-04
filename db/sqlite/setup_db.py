import argparse
import sqlite3
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from data_pipeline.pipeline import run_pipeline  # noqa: E402


DEFAULT_DB_PATH = PROJECT_ROOT / "db/sqlite/data.db"
DEFAULT_MONSTERS_JSON = PROJECT_ROOT / "data/documents/monsters.json"
DEFAULT_SCRAPED_MONSTERS_JSON = PROJECT_ROOT / "monster_scrapping/monsters.json"
DEFAULT_PIPELINE_OUTPUT_DIR = PROJECT_ROOT / "data/pipeline/runs"
DEFAULT_ADVENTURES_DIR = PROJECT_ROOT / "data/world/adventures"


def create_schema(conn: sqlite3.Connection) -> None:
    """Create the adventure schema; the data pipeline owns monster tables."""
    conn.execute("""
    CREATE TABLE IF NOT EXISTS adventures (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    goals TEXT NOT NULL,
    monsters TEXT NOT NULL,
    characters TEXT NOT NULL,
    locations TEXT NOT NULL,
    items TEXT NOT NULL,
    tags TEXT NOT NULL  
    );
    """)
    conn.commit()


def reset_schema(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS adventures")
    conn.execute("DROP TABLE IF EXISTS rejected_records")
    conn.execute("DROP TABLE IF EXISTS monster_sources")
    conn.execute("DROP TABLE IF EXISTS monsters")
    conn.execute("DROP TABLE IF EXISTS ingestion_runs")
    conn.commit()


def load_adventures(
    conn: sqlite3.Connection,
    adventures_dir: str | Path = DEFAULT_ADVENTURES_DIR,
) -> None:
    insert_sql = """
      INSERT OR REPLACE INTO adventures
      (id, name, description, goals, monsters, characters, locations, items, tags)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    for adventure_dir in sorted(Path(adventures_dir).iterdir()):
        if not adventure_dir.is_dir():
            continue

        adventure_path = adventure_dir / f"{adventure_dir.name}.json"
        if not adventure_path.exists():
            continue

        with adventure_path.open(encoding="utf-8") as file:
            adventure = json.load(file)

        conn.execute(insert_sql, (
            adventure["id"],
            adventure["name"],
            adventure.get("description"),
            json.dumps(adventure["goals"]),
            json.dumps(adventure["monsters"]),
            json.dumps(adventure["characters"]),
            json.dumps(adventure["locations"]),
            json.dumps(adventure["items"]),
            json.dumps(adventure["tags"]),
        ))

    conn.commit()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create and populate the Call To AIdventure SQLite database."
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="SQLite database path.",
    )
    parser.add_argument(
        "--monsters-json",
        type=Path,
        default=DEFAULT_MONSTERS_JSON,
        help="Monster source JSON path.",
    )
    parser.add_argument(
        "--scraped-monsters-json",
        type=Path,
        default=DEFAULT_SCRAPED_MONSTERS_JSON,
        help="Scraped monster source JSON path.",
    )
    parser.add_argument(
        "--pipeline-output-dir",
        type=Path,
        default=DEFAULT_PIPELINE_OUTPUT_DIR,
        help="Directory for raw, clean, rejected and manifest outputs.",
    )
    parser.add_argument(
        "--adventures-dir",
        type=Path,
        default=DEFAULT_ADVENTURES_DIR,
        help="Adventure source directory.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate supported tables before loading data.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    conn = sqlite3.connect(args.db_path)
    if args.reset:
        reset_schema(conn)
    create_schema(conn)
    load_adventures(conn, args.adventures_dir)
    conn.close()
    result = run_pipeline(
        curated_path=args.monsters_json,
        scraped_path=args.scraped_monsters_json,
        output_dir=args.pipeline_output_dir,
        db_path=args.db_path,
    )
    print(
        "Database created and game data loaded. "
        f"Monster pipeline run: {result.manifest.run_id} "
        f"({result.manifest.merged} merged, {result.manifest.rejected} rejected)."
    )


if __name__ == "__main__":
    main()
