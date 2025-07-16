import json
from pydantic import BaseModel, Field, ValidationError
import re

class Player(BaseModel):
    
    name: str
    race: str
    p_class : str
    gold: int
    hp: int = Field(default=10)
    xp: int = Field(default=0)
    gender: str = Field(default="male")
    
    def get_summary(self) -> str :
        return f"Name: {self.name} \n Gender: {self.gender} \n Race: {self.race} \n Class: {self.p_class} \n Gold: {self.gold} coins"

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


#region Creation

def prompt_name() -> str:
    pattern = re.compile(r'^[A-Za-z ]+$')
    while True:
        name = input("Enter your character's name: ").strip()
        if not name:
            print("Name cannot be empty.")
        elif not pattern.match(name):
            print("Name can only contain letters and spaces.")
        else:
            return name

def prompt_choice(prompt: str, options: dict) -> str:
    """
    options: mapping of accepted input -> canonical value
    e.g. {"1": "Human", "human": "Human", ...}
    """
    choices_str = ", ".join(f"{k.upper()}" for k in sorted(set(options.values())))
    keys_display = []
    # build something like "[1] Human, [2] Elf, [3] Dwarf"
    seen = {}
    for key,val in options.items():
        if val not in seen.values():
            # find a numeric key
            num = next((k for k,v in options.items() if v == val and k.isdigit()), None)
            keys_display.append(f"[{num}] {val}")
            seen[key] = val
    prompt_full = f"{prompt} ({'; '.join(keys_display)}): "
    while True:
        choice = input(prompt_full).strip().lower()
        if choice in options:
            return options[choice]
        else:
            print("Invalid choice. Please try again.")

def main():
    print("### Character Creation ###")
    name = prompt_name()

    race_map = {
        "1": "Human", "human": "Human",
        "2": "Elf",   "elf":   "Elf",
        "3": "Dwarf", "dwarf": "Dwarf",
    }
    race = prompt_choice("Choose your race", race_map)

    class_map = {
        "1": "Fighter", "fighter": "Fighter",
        "2": "Rogue",   "rogue":   "Rogue",
        "3": "Wizard",  "wizard":  "Wizard",
    }
    p_class = prompt_choice("Choose your class", class_map)

    gender_map = {
        "1": "Male",   "male":   "Male",
        "2": "Female", "female": "Female",
    }
    gender = prompt_choice("Choose your gender", gender_map)

    # defaults
    gold = 0
    xp = 0
    hp_by_class = {"Fighter": 30, "Rogue": 25, "Wizard": 20}
    hp = hp_by_class[p_class]

    try:
        player = Player(
            name=name,
            race=race,
            p_class=p_class,
            gender=gender,
            gold=gold,
            hp=hp,
            xp=xp
        )
    except ValidationError as e:
        print("Failed to create character:", e)
        return

    print("\nCharacter created successfully!")
    print(f"  Name : {player.name}")
    print(f"  Race : {player.race}")
    print(f"  Class: {player.p_class}")
    print(f"  Gender: {player.gender}")
    print(f"  Gold : {player.gold}")
    print(f"  HP   : {player.hp}")
    print(f"  XP   : {player.xp}")
    
    save_player(player)

if __name__ == "__main__":
    main()
