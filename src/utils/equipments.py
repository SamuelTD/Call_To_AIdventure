from pydantic import Field
from utils.serialization import SerializableModel

class Equipmnent(SerializableModel):
    
    name: str
    id: str = Field(default="eqp_00")
    
class Weapon(Equipmnent):
    
    min_dmg: int = Field(default=1)
    max_dmg: int = Field(default=10)