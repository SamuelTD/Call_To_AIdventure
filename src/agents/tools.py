from langchain_core.tools import Tool


def combat_tool(enemy: str) -> dict:
    return {"action": "combat", "enemy": enemy}


def nothing_tool(_: str) -> dict:
    return {"action": "continue"}


def heal_tool(amount: int) -> dict:
    return {"action": "continue"}


tools = [
    Tool(
        name="combat",
        func=combat_tool,
        description="When the player is facing a monster, start combat against that monster ; arg monster name",
        return_direct=True,
    ),
    Tool(
        name="nothing",
        func=nothing_tool,
        description="Return nothing, do nothing.",
        return_direct=True,
    ),
    Tool(
        name="heal",
        func=heal_tool,
        description="When the player should regain health ; arg heal amount",
        return_direct=True,
    ),
]