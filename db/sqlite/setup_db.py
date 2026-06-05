import argparse
import sqlite3
import json
import re
from pathlib import Path


def parse_bonus(value: str) -> int:
    """
    Parse a stat bonus string like '+2', '-1', or even malformed inputs,
    extracting the signed integer portion. Falls back to 0 if no match.
    """
    if not isinstance(value, str) or not value:
        return 0
    # Find a sign (+/-) followed by digits
    match = re.search(r"([+-]\d+)", value)
    if match:
        return int(match.group(1))
    # Try to convert directly
    try:
        return int(value)
    except ValueError:
        return 0

def parse_challenge_rating(value: str) -> int:
    if not isinstance(value, str) or not value:
        return 1
    try:
        return int(value)
    except ValueError:
        return 0

def create_schema(conn: sqlite3.Connection) -> None:
    """
    Create the monsters table with appropriate columns.
    """
    conn.execute("""
    CREATE TABLE IF NOT EXISTS monsters (
      name TEXT PRIMARY KEY,
      armor TEXT,
      HP TEXT,
      challenge_rating TEXT,
      strength INTEGER,
      dexterity INTEGER,
      constitution INTEGER,
      intelligence INTEGER,
      wisdom INTEGER,
      charisma INTEGER,
      description TEXT,
      gold_loot_min INTEGER,
      gold_loot_max INTEGER,
      items_loot TEXT 
    );
    """
    )
    
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
    conn.execute("DROP TABLE IF EXISTS monsters")
    conn.commit()


def load_monsters(
    conn: sqlite3.Connection,
    json_path: str = "data/documents/monsters.json"
) -> None:
    """
    Read the JSON file of monster entries and insert them into the SQLite database,
    parsing signed stat bonuses correctly.
    """
    with open(json_path, encoding="utf-8") as f:
        monsters = json.load(f)

    insert_sql = """
      INSERT OR REPLACE INTO monsters
      (name, armor, HP, challenge_rating,
       strength, dexterity, constitution,
       intelligence, wisdom, charisma, description, gold_loot_min, gold_loot_max, items_loot)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    for m in monsters:
        gold_min = 0
        gold_max = 0
        loot = []
        try:
            gold_min = m.get("gold_loot")[0]
            gold_max = m.get("gold_loot")[1]
            
        except (TypeError, IndexError):
            gold_min = 0
            gold_max = 1
        
        try:
            loot = json.dumps(m.get("items_loot"))
        except TypeError:
            loot = json.dumps(["debug loot item"])
        conn.execute(insert_sql, (
            m.get("name"),
            m.get("armor"),
            m.get("HP"),
            parse_challenge_rating(m.get("challenge_rating")),
            parse_bonus(m.get("strength", "0")),
            parse_bonus(m.get("dexterity", "0")),
            parse_bonus(m.get("constitution", "0")),
            parse_bonus(m.get("intelligence", "0")),
            parse_bonus(m.get("wisdom", "0")),
            parse_bonus(m.get("charisma", "0")),
            m.get("description"),
            gold_min,
            gold_max,
            loot
            ))
    conn.commit()


def load_adventures(
    conn: sqlite3.Connection,
    adventures_dir: str = "data/world/adventures",
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
        default="db/sqlite/data.db",
        help="SQLite database path.",
    )
    parser.add_argument(
        "--monsters-json",
        default="data/documents/monsters.json",
        help="Monster source JSON path.",
    )
    parser.add_argument(
        "--adventures-dir",
        default="data/world/adventures",
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
    load_monsters(conn, args.monsters_json)
    load_adventures(conn, args.adventures_dir)
    conn.close()
    print("Database created and game data loaded.")


if __name__ == "__main__":
    main()
