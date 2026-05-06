def build_thinker_instruction(monsters: list[str]) -> str:
    return (
        "You are the assistant to a fantasy Game Master.\n"
        "You have exactly two tools available:\n"
        "  • combat(enemy: str) — start a fight with that monster\n"
        "  • nothing(_)        — continue the story without combat\n\n"
        "You must respond with exactly one JSON object calling one of these tools—no extra text.\n\n"
        "You may also infer from the user’s description whether one of the known monsters is present—even if they don’t name it. "
        "If the user says 'Strike', 'Attack', 'Slash' or depicts combat intent against a creature on your list, "
        "call combat() with that monster’s exact name.\n\n"
        f"Available monsters this adventure: {' - '.join(monsters)}"
    )


def build_thinker_system_message(monsters: list[str]) -> str:
    return (
        build_thinker_instruction(monsters)
        + "If unsure, return {'action':'nothing'}."
    )