import json
from pydantic import BaseModel, Field
from typing import List, Dict

class Player(BaseModel):
    
    name: str
    race: str
    p_class : str
    gold: int
    hp: int = Field(default=10)
    xp: int = Field(default=0)

file_path = "data/world/other/player.json"

def load_player(path=file_path) -> Player:
    try:
        data = json.load(open(path))
        return Player(**data)
    except FileNotFoundError:
        player = Player(name="Stan", race="human", p_class="fighter", gold=10, hp=20, xp=0)
        save_player(player)
        return player

def save_player(player: Player, path=file_path):
    with open(path, "w") as f:
        json.dump(player.model_dump(), f, indent=2)
