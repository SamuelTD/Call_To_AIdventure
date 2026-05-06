from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class AmountArgs(BaseModel):
    amount: int | str = Field(
        description="Health amount as an integer or numeric string."
    )


class CombatArgs(BaseModel):
    enemy: str = Field(description="Exact monster name to fight.")


def combat_tool(enemy: str) -> dict:
    return {"action": "combat", "enemy": enemy}


def nothing_tool() -> dict:
    return {"action": "continue"}


def heal_tool(amount: int) -> dict:
    return {"action": "heal", "amount": amount}


def deal_damage_tool(amount: int) -> dict:
    return {"action": "damage", "amount": amount}


tools = [
    StructuredTool.from_function(
        func=combat_tool,
        name="combat",
        args_schema=CombatArgs,
        description="When the player is facing a monster, start combat against that monster ; arg monster name",
        return_direct=True,
    ),
    StructuredTool.from_function(
        func=nothing_tool,
        name="nothing",
        description="Return nothing, do nothing.",
        return_direct=True,
    ),
    StructuredTool.from_function(
        func=heal_tool,
        name="heal",
        args_schema=AmountArgs,
        description="When the player should regain health ; arg heal amount",
        return_direct=True,
    ),
    StructuredTool.from_function(
        func=deal_damage_tool,
        name="deal_damage",
        args_schema=AmountArgs,
        description="When the player should lose health because of narrative danger ; arg damage amount",
        return_direct=True,
    ),
]
