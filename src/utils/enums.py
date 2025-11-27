from enum import Enum, auto

class StrEnum(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()

class CharacterClass(StrEnum):
    
    FIGHTER   = auto()
    ROGUE = auto()
    WIZARD  = auto()
    
class PlayerAction(StrEnum):
    
    ATTACK = auto()
    DEFEND = auto()
    USE_ITEM = auto()
    FIRE_BOLT = auto()
