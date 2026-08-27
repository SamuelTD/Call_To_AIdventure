from langchain_core.prompts import ChatPromptTemplate


CHOOSER_TEMPLATE = ChatPromptTemplate.from_template(
    "You are a role player in a fantasy adventure.\n"
    "Here is the current state of your character:\n"
    "{player_summary}\n\n"
    "Here is the current narrative context:\n"
    "{context}\n\n"
    "Relevant world lore:\n"
    "{rag_context}\n\n"
    "Return exactly three possible next actions for the player.\n"
    "Rules:\n"
    "- Each action must be at most 6 words long.\n"
    "- The three actions must be meaningfully different.\n"
    "- Only offer actions that make sense in the immediate current situation.\n"
    "- Use retrieved lore only when relevant to the immediate current situation.\n"
    "- Do not offer actions involving characters or locations outside the current adventure scope.\n"
    "- Only offer spellcasting if the class is wizard.\n"
    "- If another character is actively speaking, one action may be dialogue.\n"
    "- Do not repeat or closely paraphrase these previous choices:\n"
    "{last_choices}\n"
)

CHOOSER_TEMPLATE_FR = ChatPromptTemplate.from_template(
    "Tu incarnes un joueur dans une aventure fantastique.\n"
    "Voici l'état actuel de ton personnage :\n{player_summary}\n\n"
    "Voici le contexte narratif actuel :\n{context}\n\n"
    "Connaissances pertinentes sur l'univers :\n{rag_context}\n\n"
    "Retourne exactement trois actions possibles en français pour le joueur.\n"
    "Règles :\n"
    "- Chaque action comporte au maximum 6 mots.\n"
    "- Les trois actions doivent être clairement différentes.\n"
    "- Ne propose que des actions cohérentes avec la situation immédiate.\n"
    "- N'utilise les connaissances récupérées que si elles sont pertinentes.\n"
    "- Ne propose aucune action impliquant un personnage ou lieu extérieur à l'aventure.\n"
    "- Ne propose de lancer un sort que si la classe est magicien.\n"
    "- Si un autre personnage parle, une action peut être une réplique.\n"
    "- Ne répète ni ne reformule de trop près ces choix précédents :\n{last_choices}\n"
)
