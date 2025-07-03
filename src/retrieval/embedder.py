# src/retrieval/embedder.py

import os
import requests
from typing import List

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "mxbai-embed-large:latest")

def embed(text: str) -> List[float]:
    url = f"{OLLAMA_HOST}/v1/embeddings"
    payload = {
        "model": EMBED_MODEL,
        "input": [text]
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    embeddings = resp.json()["data"][0]["embedding"]
    return embeddings