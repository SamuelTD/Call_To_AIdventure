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

# Le modèle d'embedding (doit être le même que celui utilisé pour la création).
EMBEDDING_MODEL = "mxbai-embed-large:latest"

# Le modèle de LLM à utiliser pour la génération de la réponse.
LLM_MODEL = "llama3.2:latest"

# Initialise le client Ollama pour les embeddings
ollama_embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

# Vector stores 

vectorstore_char = Chroma(
    client=chromadb.PersistentClient(path="db/chroma"),
    collection_name=CHAR_COL,
    embedding_function=ollama_embeddings
)

vectorstore_loc = Chroma(
    client=chromadb.PersistentClient(path="db/chroma"),
    collection_name=LOC_COL,
    embedding_function=ollama_embeddings
)

# Retrievers
lulu_retriever = vectorstore_char.as_retriever(search_kwargs={"k":1, "filter": {
            "$and": [
                {"type": {"$eq": "character"}},
                {"id":   {"$eq": "lulu_the_wise"}}
            ]
        }})

char_retriever = vectorstore_char.as_retriever(search_kwargs={"k": 5, "filter": {"id" : {"$ne": "lulu_the_wise"}}})

loc_retriever = vectorstore_loc.as_retriever(search_kwargs={"k": 3})

# Model with OLLAMA
llm = ChatOllama(model=LLM_MODEL)

# Prompt Template

template = """
{lulu}

Now, using those scrolls *and* the following additional world‐lore:

{context_char}
{context_loc}

Answer with Lulu’s trademark sass…

Question: {question}
"""

prompt = ChatPromptTemplate.from_template(template)

# RAG chain

rag_chain = (
    {"lulu": lulu_retriever, "context_char": char_retriever, "context_loc": loc_retriever, "question": RunnablePassthrough()} # Étape de recherche (Retrieval)
    | prompt                                                  # Étape d'augmentation (Augmented)
    | llm                                                     # Étape de génération (Generation)
    | StrOutputParser()                                       # Parse la sortie du LLM en chaîne de caractères
)

# Main loop

if __name__ == "__main__":
   
    # doc = retriever.get_relevant_documents(user_question)
    # print("Retrieved chunks: ", doc)
    
    print("\n--- Game Master v0.1 ---")
    print("Ask question about a known character.")

    
    while True:
        user_question = input("\nYou: ")
        if user_question.lower() == "exit":
            break

        print("Assistant: ...")
        # Invoque la chaîne RAG avec la question de l'utilisateur
        answer = rag_chain.invoke(user_question)
        print(f"\rAssistant: {answer}")
