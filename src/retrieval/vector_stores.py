from langchain_chroma import Chroma
from retrieval.client import client as chroma_client
from retrieval.embedder import ollama_embeddings

CHAR_COL = "characters"
LOC_COL = "locations"

vectorstore_char = Chroma(
    client=chroma_client,
    collection_name=CHAR_COL,
    embedding_function=ollama_embeddings,
)

vectorstore_loc = Chroma(
    client=chroma_client,
    collection_name=LOC_COL,
    embedding_function=ollama_embeddings,
)