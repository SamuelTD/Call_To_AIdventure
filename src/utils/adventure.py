from typing import List, Optional
from pydantic import BaseModel, Field
import json
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

file_path = os.getenv("DB_PATH")

class Adventure(BaseModel):
    id: str = Field(..., description="Unique identifier for the adventure module")
    name: str = Field(..., description="Title of the adventure module")
    description: Optional[str] = Field(None, description="Brief summary or blurb")
    monsters: List[str] = Field(..., description="List of monster names referenced by this module")
    npcs: List[str] = Field(..., description="List of NPC names referenced by this module")
    locations: List[str] = Field(..., description="List of location names referenced by this module")
    items: List[str] = Field(default_factory=list, description="Optional list of item names used in this module")
    tags: List[str] = Field(default_factory=list, description="Optional tags for categorization")
    

def save_adventure(title: str) -> None:
    
    with open(f"data/world/adventures/{title}/{title}.json", "r") as file:
        data = json.load(file)
        
    conn = sqlite3.connect(file_path)        
   
    conn.execute(
        '''INSERT OR REPLACE INTO adventures
           (id, name, description, monsters, npcs, locations, items, tags)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            data['id'],
            data['name'],
            data.get('description'),
            json.dumps(data['monsters']),
            json.dumps(data['npcs']),
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
        'SELECT id, name, description, monsters, npcs, locations, items, tags FROM adventures WHERE id = ?',
        (adv_id,)
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        raise KeyError(f"Adventure with id '{adv_id}' not found")

    id_, name, desc, monsters, npcs, locations, items, tags = row
    payload = {
        'id': id_,
        'name': name,
        'description': desc,
        'monsters': json.loads(monsters),
        'npcs': json.loads(npcs),
        'locations': json.loads(locations),
        'items': json.loads(items),
        'tags': json.loads(tags)
    }
    
    return Adventure(**payload)

if __name__=="__main__":
    save_adventure("emerald_sword")