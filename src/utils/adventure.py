from typing import List, Optional
from pydantic import Field
from utils.serialization import SerializableModel
import json
import sqlite3
from dotenv import load_dotenv
from pathlib import Path
from utils.pathing import env_project_path

load_dotenv()
ROOT_DIR = Path(__file__).resolve().parents[2]
file_path = env_project_path("DB_PATH", "db/sqlite/data.db")


class AdventureCharacters(SerializableModel):
    active: List[str] = Field(
        default_factory=list,
        description="Character IDs actively present in the current adventure setup.",
    )
    referenceable: List[str] = Field(
        default_factory=list,
        description="Character IDs that may be retrieved as world lore references.",
    )


class AdventureLocations(SerializableModel):
    available: List[str] = Field(
        default_factory=list,
        description="Location IDs available to this adventure.",
    )
    start: Optional[str] = Field(
        default=None,
        description="Location ID where the adventure starts.",
    )


class Adventure(SerializableModel):
    id: str = Field(..., description="Unique identifier for the adventure module")
    name: str = Field(..., description="Title of the adventure module")
    description: Optional[str] = Field(None, description="Brief summary or blurb")
    goals: List[str] = Field(..., description="The list of objectives the player needs to accomplish for the Adventure to be considred won.")
    monsters: List[str] = Field(..., description="List of monster names referenced by this module")
    characters: AdventureCharacters = Field(default_factory=AdventureCharacters)
    locations: AdventureLocations = Field(default_factory=AdventureLocations)
    items: List[str] = Field(default_factory=list, description="Optional list of item names used in this module")
    tags: List[str] = Field(default_factory=list, description="Optional tags for categorization")


def build_adventure_payload(
    id_: str,
    name: str,
    desc: Optional[str],
    goals: str,
    monsters: str,
    characters: str,
    locations: str,
    items: str,
    tags: str,
) -> dict:
    return {
        'id': id_,
        'name': name,
        'description': desc,
        'goals': json.loads(goals),
        'monsters': json.loads(monsters),
        'characters': json.loads(characters),
        'locations': json.loads(locations),
        'items': json.loads(items),
        'tags': json.loads(tags)
    }
    

def save_adventure(title: str) -> None:
    
    with open(f"data/world/adventures/{title}/{title}.json", "r") as file:
        data = json.load(file)
        
    conn = sqlite3.connect(file_path)        
   
    conn.execute(
        '''INSERT OR REPLACE INTO adventures
           (id, name, description, goals, monsters, characters, locations, items, tags)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            data['id'],
            data['name'],
            data.get('description'),
            json.dumps(data['goals']),
            json.dumps(data['monsters']),
            json.dumps(data['characters']),
            json.dumps(data['locations']),
            json.dumps(data['items']),
            json.dumps(data['tags'])
        )
    )
    conn.commit()
    conn.close()

def load_adventure(adv_id: str) -> Adventure:
    
    conn = sqlite3.connect(file_path)    
    
    cur = conn.execute(
        'SELECT id, name, description, goals, monsters, characters, locations, items, tags FROM adventures WHERE id = ?',
        (adv_id,)
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        raise KeyError(f"Adventure with id '{adv_id}' not found")

    id_, name, desc, goals, monsters, characters, locations, items, tags = row
    payload = build_adventure_payload(
        id_, name, desc, goals, monsters, characters, locations, items, tags
    )
    
    return Adventure(**payload)

def load_adv_intro(id: str) -> str:
    with open(ROOT_DIR / f"data/world/adventures/{id}/intro.txt", "r") as f:
        intro = f.read()
        
    return intro

def load_adv_outro(id: str) -> str:
    with open(ROOT_DIR / f"data/world/adventures/{id}/outro.txt", "r") as f:
        outro = f.read()
        
    return outro

def load_all_adventures() -> List[Adventure]:
    """
    Fetch all adventures from the database and return them as a list of Adventure instances.
    """
    conn = sqlite3.connect(file_path)
    cur = conn.execute(
        'SELECT id, name, description, goals, monsters, characters, locations, items, tags '
        'FROM adventures'
    )
    rows = cur.fetchall()
    conn.close()

    adventures: List[Adventure] = []
    for row in rows:
        id_, name, desc, goals, monsters, characters, locations, items, tags = row
        payload = build_adventure_payload(
            id_, name, desc, goals, monsters, characters, locations, items, tags
        )
        adventures.append(Adventure(**payload))

    return adventures

if __name__=="__main__":
    save_adventure("emerald_sword")
    save_adventure("l_epee_d_emeraude")
    save_adventure("test_adv")
