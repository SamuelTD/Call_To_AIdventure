from retrieval.chunker import chunk_player_json_file
from retrieval.client import upsert_chunks
from retrieval.embedder import embed
import os


# DEPRECATED

URL = "data/world/other/player.json"
COLLECTION = "player"

def ingest_player():
    
    chunks = chunk_player_json_file(URL)

    # 2) Embed each chunk
    embeddings = []
    for idx, chunk in enumerate(chunks):
        vec = embed(chunk["page_content"])
        embeddings.append(vec)

    # 3) Upsert into ChromaDB
    upsert_chunks(COLLECTION, embeddings, chunks)

