from langchain_core.prompts import ChatPromptTemplate


SUMMARY_TEMPLATE = ChatPromptTemplate.from_template(
    "You are a concise summarizer for fantasy narrative. "
    "You write in the past tense, in the third person and replace the 2nd person by 'the player'. "
    "Condense the following narrative context into a single paragraph starting with "
    "'Summary of the story :':\n\n"
    "{context}"
)