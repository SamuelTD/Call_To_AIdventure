import logging
import time
import requests
from typing import List
from langchain_ollama import OllamaEmbeddings
from agents.runtime_config import AIRuntimeConfig
from observability.metrics import RAG_EMBEDDING_REQUESTS, RAG_EMBEDDING_DURATION

logger = logging.getLogger(__name__)
AI_CONFIG = AIRuntimeConfig.from_env()
OLLAMA_HOST = AI_CONFIG.ollama_host
EMBED_MODEL = AI_CONFIG.embedding_model

ollama_embeddings = OllamaEmbeddings(model=EMBED_MODEL)


class EmbeddingRequestError(RuntimeError):
    """Raised when the configured embedding provider cannot return an embedding."""


def embed(text: str) -> List[float]:
    """
    Send text to Ollama with bounded retries and no content logging.
    """
    url = f"{OLLAMA_HOST}/v1/embeddings"
    payload = {
        "model": EMBED_MODEL,
        "input": [text]
    }
    started = time.perf_counter()
    resp = None
    for attempt in range(1, AI_CONFIG.embedding_max_attempts + 1):
        try:
            resp = requests.post(url, json=payload, timeout=AI_CONFIG.embedding_timeout_seconds)
            resp.raise_for_status()
            break
        except requests.RequestException as exc:
            if attempt >= AI_CONFIG.embedding_max_attempts:
                RAG_EMBEDDING_REQUESTS.labels(status="error").inc()
                message = (
                    f"Embedding request failed after {attempt} attempts "
                    f"against {url}: {exc}"
                )
                logger.warning(message)
                logger.debug("Embedding request traceback", exc_info=True)
                raise EmbeddingRequestError(message) from exc
            time.sleep(min(0.25 * (2 ** (attempt - 1)), 2.0))
    RAG_EMBEDDING_DURATION.observe(time.perf_counter() - started)

    data = resp.json()
    if "data" not in data or not data["data"]:
        RAG_EMBEDDING_REQUESTS.labels(status="invalid_response").inc()
        raise ValueError("No embedding data in response")

    embedding = data["data"][0].get("embedding")
    if not embedding:
        RAG_EMBEDDING_REQUESTS.labels(status="invalid_response").inc()
        raise ValueError("Embedding missing in response")

    RAG_EMBEDDING_REQUESTS.labels(status="success").inc()
    return embedding
