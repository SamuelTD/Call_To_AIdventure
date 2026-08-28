import json
from pydantic import Field
from utils.serialization import SerializableModel
from utils.enums import CharacterClass, PlayerAction
from utils.equipments import Weapon
from pathlib import Path

RACE_OPTIONS = ["Human", "Elf", "Dwarf", "Halfling"]
GENDER_OPTIONS = ["Female", "Male"]

CLASS_LOADOUTS = {
    CharacterClass.FIGHTER: {
        "gold": 10,
        "max_hp": 30,
        "weapon": Weapon(name="Longsword", min_dmg=2, max_dmg=7),
        "strength": 3,
        "agility": 1,
        "arcana": 0,
        "actions": [PlayerAction.ATTACK, PlayerAction.DEFEND],
    },
    CharacterClass.ROGUE: {
        "gold": 14,
        "max_hp": 24,
        "weapon": Weapon(name="Twin Daggers", min_dmg=1, max_dmg=6),
        "strength": 1,
        "agility": 3,
        "arcana": 0,
        "actions": [PlayerAction.ATTACK, PlayerAction.DEFEND],
    },
    CharacterClass.WIZARD: {
        "gold": 8,
        "max_hp": 20,
        "weapon": Weapon(name="Quarterstaff", min_dmg=1, max_dmg=5),
        "strength": 0,
        "agility": 1,
        "arcana": 4,
        "actions": [PlayerAction.ATTACK, PlayerAction.DEFEND],
    },
}

class Player(SerializableModel):
    
    name: str
    race: str
    p_class : CharacterClass
    gold: int = Field(default=10)
    max_hp: int = Field(default=10)
    hp: int
    xp: int = Field(default=0)
    gender: str = Field(default="male")
    actions: list[PlayerAction] = Field(default_factory=lambda: [PlayerAction.ATTACK, PlayerAction.DEFEND])
    inventory: list = Field(default_factory=list)
    weapon: Weapon = Field(default_factory=lambda: Weapon(name="Sword", min_dmg=2, max_dmg=6))
    strength: int = Field(default=0)
    agility: int = Field(default=0)
    arcana: int = Field(default=0)
    
    def get_summary(self) -> str :
        return f"Name: {self.name} \n Gender: {self.gender} \n Race: {self.race} \n Class: {self.p_class} \n Gold: {self.gold} coins \n\
            Weapon : {self.weapon.name}"

ROOT_DIR = Path(__file__).resolve().parents[2]
file_path = ROOT_DIR / "data/world/other/player.json"

def get_character_creation_options() -> dict:
    return {
        "races": RACE_OPTIONS,
        "classes": [character_class.value for character_class in CharacterClass],
        "genders": GENDER_OPTIONS,
    }

def create_player(
    *,
    name: str,
    race: str,
    p_class: str | CharacterClass,
    gender: str,
) -> Player:
    try:
        character_class = CharacterClass(p_class)
    except ValueError as exc:
        raise ValueError("Invalid class") from exc

    if race not in RACE_OPTIONS:
        raise ValueError("Invalid race")
    if gender not in GENDER_OPTIONS:
        raise ValueError("Invalid gender")

    clean_name = " ".join(str(name or "").split())
    if not clean_name:
        raise ValueError("Name is required")

    loadout = CLASS_LOADOUTS[character_class]
    max_hp = loadout["max_hp"]

    return Player(
        name=clean_name,
        race=race,
        p_class=character_class,
        gender=gender,
        gold=loadout["gold"],
        max_hp=max_hp,
        hp=max_hp,
        xp=0,
        actions=list(loadout["actions"]),
        inventory=[],
        weapon=loadout["weapon"].model_copy(deep=True),
        strength=loadout["strength"],
        agility=loadout["agility"],
        arcana=loadout["arcana"],
    )

def load_player(path=file_path) -> Player:
    try:
        data = json.load(open(path))
        return Player(**data)
    except FileNotFoundError:
        player = create_player(
            name="Stan",
            race="Human",
            p_class=CharacterClass.FIGHTER,
            gender="Male",
        )
        save_player(player)
        return player

def save_player(player: Player, path=file_path):
    data = player.model_dump(mode="json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
