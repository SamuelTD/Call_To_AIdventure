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
