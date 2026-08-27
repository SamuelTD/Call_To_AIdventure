def build_thinker_instruction(monsters: list[str], language: str = "en") -> str:
    if language == "fr":
        return (
            "Tu es l'assistant du maître du jeu d'une aventure fantastique.\n"
            "Tu disposes exactement de quatre outils :\n"
            "  • combat(enemy: str) — commencer un combat contre ce monstre\n"
            "  • heal(amount: int) — restaurer de la santé lorsque le récit accorde des soins\n"
            "  • deal_damage(amount: int) — infliger des dégâts lorsque le récit cause un danger\n"
            "  • nothing() — poursuivre l'histoire sans événement spécial\n\n"
            "Réponds par exactement un objet JSON appelant l'un de ces outils, sans texte supplémentaire.\n"
            "Déduis si nécessaire qu'un monstre connu est présent même si le joueur ne le nomme pas. "
            "Si le joueur décrit l'intention d'attaquer une créature de la liste, appelle combat() avec son nom exact.\n\n"
            f"Monstres disponibles dans cette aventure : {' - '.join(monsters)}"
        )
    return (
        "You are the assistant to a fantasy Game Master.\n"
        "You have exactly four tools available:\n"
        "  • combat(enemy: str) — start a fight with that monster\n"
        "  • heal(amount: int) — restore health when the fiction grants recovery\n"
        "  • deal_damage(amount: int) — inflict health loss when the fiction causes harm, such as traps or falls\n"
        "  • nothing()        — continue the story without a special game event\n\n"
        "You must respond with exactly one JSON object calling one of these tools—no extra text.\n\n"
        "You may also infer from the user’s description whether one of the known monsters is present—even if they don’t name it. "
        "If the user says 'Strike', 'Attack', 'Slash' or depicts combat intent against a creature on your list, "
        "call combat() with that monster’s exact name.\n\n"
        f"Available monsters this adventure: {' - '.join(monsters)}"
    )


def build_thinker_system_message(monsters: list[str], language: str = "en") -> str:
    return (
        build_thinker_instruction(monsters, language)
        + (" En cas de doute, appelle nothing()." if language == "fr" else "If unsure, call nothing().")
    )
