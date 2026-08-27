from langchain_core.prompts import ChatPromptTemplate


SUMMARY_TEMPLATE = ChatPromptTemplate.from_template(
    "You are a concise summarizer for fantasy narrative. "
    "You write in the past tense, in the third person and replace the 2nd person by 'the player'. "
    "Condense the following narrative context into a single paragraph starting with "
    "'Summary of the story :':\n\n"
    "{context}"
)

SUMMARY_TEMPLATE_FR = ChatPromptTemplate.from_template(
    "Tu résumes avec concision un récit fantastique en français. "
    "Écris au passé et à la troisième personne, en remplaçant la deuxième personne par « le joueur ». "
    "Condense le contexte narratif suivant en un seul paragraphe commençant par "
    "« Résumé de l'histoire : » :\n\n{context}"
)
