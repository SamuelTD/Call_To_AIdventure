# -*- coding: utf-8 -*-

import chromadb
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

# --- 1. Configuration ---

# Le nom de la collection que nous avons créée dans le script précédent.
COLLECTION_NAME = "characters"
# Le modèle d'embedding (doit être le même que celui utilisé pour la création).
EMBEDDING_MODEL = "mxbai-embed-large:latest"
# Le modèle de LLM à utiliser pour la génération de la réponse.
LLM_MODEL = "llama3.2:latest"

# --- 2. Initialisation des composants LangChain ---

print("Initialisation des composants LangChain...")

# Initialise le client Ollama pour les embeddings
ollama_embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

# Initialise le client ChromaDB pour se connecter à la base de données existante.
# Le chemin doit correspondre à l'endroit où la DB a été créée par module5_creation_db.py
# (qui est dans le même dossier 'code')
vectorstore = Chroma(
    client=chromadb.PersistentClient(path="db/chroma"),
    collection_name=COLLECTION_NAME,
    embedding_function=ollama_embeddings
)

# Crée un retriever à partir du vectorstore.
# Le retriever est responsable de la recherche des documents pertinents.
retriever = vectorstore.as_retriever(search_kwargs={"k": 3}) # Récupère les 3 chunks les plus pertinents

# Initialise le modèle de chat Ollama
llm = ChatOllama(model=LLM_MODEL)

# --- 3. Définition du prompt RAG ---

# Le template du prompt pour le LLM.
# Il inclut le contexte récupéré et la question de l'utilisateur.
template = """You are a librarian who holds scrolls containing important informations about historical figures in this world. \
    You answer questions about those figures. Your scrolls are found in the following :
{context}

Question: {question}
"""
prompt = ChatPromptTemplate.from_template(template)

# --- 4. Construction de la chaîne RAG avec LangChain Expression Language (LCEL) ---

# La chaîne RAG est construite en utilisant LCEL pour une meilleure lisibilité et modularité.
rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()} # Étape de recherche (Retrieval)
    | prompt                                                  # Étape d'augmentation (Augmented)
    | llm                                                     # Étape de génération (Generation)
    | StrOutputParser()                                       # Parse la sortie du LLM en chaîne de caractères
)

# --- 5. Boucle d'interaction ---

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
