import sqlite3
import json
import re


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
      description TEXT
    );
    """
    )
    
    conn.execute("""
    CREATE TABLE IF NOT EXISTS adventures (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    monsters TEXT NOT NULL,
    npcs TEXT NOT NULL,
    locations TEXT NOT NULL,
    items TEXT NOT NULL,
    tags TEXT NOT NULL  
    );
    """)
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
       intelligence, wisdom, charisma, description)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    for m in monsters:
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
            m.get("description")
        ))
    conn.commit()


if __name__ == "__main__":
    # Initialize and populate the database
    conn = sqlite3.connect("db/sqlite/data.db")
    create_schema(conn)
    load_monsters(conn)
    conn.close()
    print("Database created and monster stats loaded.")
