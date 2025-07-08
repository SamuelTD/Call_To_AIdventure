# -*- coding: utf-8 -*-

import chromadb
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough


# Chroma collections
CHAR_COL = "characters"
LOC_COL = "locations"
OTHER_COL = "other"

# Le modèle d'embedding (doit être le même que celui utilisé pour la création).
EMBEDDING_MODEL = "mxbai-embed-large:latest"

# Le modèle de LLM à utiliser pour la génération de la réponse.
LLM_MODEL = "artifish/llama3.2-uncensored"

# Initialise le client Ollama pour les embeddings
ollama_embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

# Vector stores 

vectorstore = Chroma(
    client=chromadb.PersistentClient(path="db/chroma"),
    collection_name=OTHER_COL,
    embedding_function=ollama_embeddings
)

# Retrievers
sonya_retriever = vectorstore.as_retriever(search_kwargs={"k":1, "filter": {
            "$and": [
                {"type": {"$eq": "character"}},
                {"id":   {"$eq": "sonya"}}
            ]
        }})

# Model with OLLAMA
llm = ChatOllama(model=LLM_MODEL)

# Prompt Template

template = """
{sonya}

Using Sonya's personnality, background and traits, answer the user input as best as you can. You will be explicit and sexual but classy and refined. \
    You are always willing to have sex. Use * * to narrate your actions. For example *sink to my knees and wrap my lips around your cock*.

User input: {question}
"""

prompt = ChatPromptTemplate.from_template(template)

# RAG chain

rag_chain = (
    {"sonya": sonya_retriever, "question": RunnablePassthrough()} # Étape de recherche (Retrieval)
    | prompt                                                  # Étape d'augmentation (Augmented)
    | llm                                                     # Étape de génération (Generation)
    | StrOutputParser()                                       # Parse la sortie du LLM en chaîne de caractères
)

# Main loop

if __name__ == "__main__":
   
    # doc = retriever.get_relevant_documents(user_question)
    # print("Retrieved chunks: ", doc)
    
    print("\n--- Game Master v0.1 ---")
    print("You're discussing with Sonya.")

    
    while True:
        user_question = input("\nYou: ")
        if user_question.lower() == "exit":
            break

        
        # Invoque la chaîne RAG avec la question de l'utilisateur
        answer = rag_chain.invoke(user_question)
        print(f"\rAssistant: {answer}")
