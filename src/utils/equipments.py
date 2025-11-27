from pydantic import BaseModel, Field, ValidationError

class Equipmnent(BaseModel):
    
    name: str
    id: str = Field(default="eqp_00")
    
class Weapon(Equipmnent):
    
    min_dmg: int = Field(default=1)
    max_dmg: int = Field(default=10)