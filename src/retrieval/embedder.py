import os
import requests
from typing import List
from langchain_ollama import OllamaEmbeddings

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "mxbai-embed-large:latest")

ollama_embeddings = OllamaEmbeddings(model=EMBED_MODEL)

def embed(text: str) -> List[float]:
    """
    Send `text` to Ollama to get back an embedding vector, with progress prints.
    """
    text_len = len(text)
    print(f"[embed] Preparing to embed text ({text_len} chars). Model: {EMBED_MODEL}")

    url = f"{OLLAMA_HOST}/v1/embeddings"
    print(f"[embed] Sending POST to {url} with payload size: 1 text item.")

    payload = {
        "model": EMBED_MODEL,
        "input": [text]
    }
    try:
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[embed] Request failed: {e}")
        if resp is not None:
            print(f"[embed] Response status: {resp.status_code}, body: {resp.text}")
        raise

    data = resp.json()
    if "data" not in data or not data["data"]:
        print(f"[embed] Unexpected response format: {data}")
        raise ValueError("No embedding data in response")

    embedding = data["data"][0].get("embedding")
    if not embedding:
        print("[embed] Embedding field missing in response data")
        raise ValueError("Embedding missing in response")

    print(f"[embed] Received embedding vector of length {len(embedding)}")
    return embedding
