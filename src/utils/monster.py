from pydantic import Field
from utils.serialization import SerializableModel
import sqlite3
from typing import Optional, Tuple, List
import os, json
from dotenv import load_dotenv

load_dotenv()

file_path = os.getenv("DB_PATH")

class Monster(SerializableModel):
    
    name: str
    armor: int
    HP: int
    max_HP: int = Field(default=1)
    challenge_rating: int
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int
    description: str
    gold_loot: Tuple[int, int] = Field(default=(0,0))
    items_loot : List[str] = Field(default=[])

def get_monster(name: str) -> Optional[Monster]:
    """
    Fetches the monster’s row from SQLite and returns a Monster pydantic object.
    Returns None if no monster with that name exists.
    """
    conn = sqlite3.connect(file_path)
    cur  = conn.execute("SELECT * FROM monsters WHERE name COLLATE NOCASE = ?", (name,))
    row  = cur.fetchone()
    cols = [col[0] for col in cur.description]
    conn.close()

    if row is None:
        return None

    # Build a dict mapping column names → values
    data = dict(zip(cols, row))
    
    # Deserialize your JSON string into a real Python list
    try:
        data["items_loot"] = json.loads(data["items_loot"])
    except (TypeError, json.JSONDecodeError):
        # fallback to an empty list (or handle as you see fit)
        data["items_loot"] = []

    # Pack gold_loot as a tuple
    data["gold_loot"] = (data["gold_loot_min"], data["gold_loot_max"])

    # Now everything lines up with your Monster model
    monster = Monster(**data)
    monster.max_HP = monster.HP
    print("MONSTER =  ", monster)
    return monster

if __name__ == "__main__":
    
    monster = get_monster("Kobold Warrior")
    print(monster.name)
