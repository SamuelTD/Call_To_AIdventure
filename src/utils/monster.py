import json
from pydantic import BaseModel, Field
import sqlite3
from typing import Optional

class Monster(BaseModel):
    
    name: str
    armor: int
    HP: int
    challenge_rating: int
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int
    description: str

file_path = "db/sqlite/monsters.db"

def get_monster(name: str) -> Optional[Monster]:
    """
    Fetches the monster’s row from SQLite and returns a Monster pydantic object.
    Returns None if no monster with that name exists.
    """
    conn = sqlite3.connect(file_path)
    cur  = conn.execute("SELECT * FROM monsters WHERE name = ?", (name,))
    row  = cur.fetchone()
    cols = [col[0] for col in cur.description]
    conn.close()

    if row is None:
        return None

    # Build a dict mapping column names → values
    data = dict(zip(cols, row))

    # Finally, construct the Monster
    monster = Monster(**data)
    return monster

if __name__ == "__main__":
    
    monster = get_monster("Aarakocra Aeromancer")
    print(monster.name)
