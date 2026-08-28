from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.errors import NotFoundError

from retrieval.schemas import LoreChunk
from utils.pathing import CHROMA_DIR


LORE_COLLECTION = "world_lore"

client = chromadb.PersistentClient(path=str(CHROMA_DIR))


def get_or_create_collection(name: str = LORE_COLLECTION) -> Collection:
    try:
        return client.get_collection(name)
    except NotFoundError:
        return client.create_collection(name=name)


def reset_collection(name: str = LORE_COLLECTION) -> None:
    try:
        client.delete_collection(name)
    except NotFoundError:
        return


def upsert_lore_chunks(
    chunks: list[LoreChunk],
    embeddings: list[list[float]],
    collection_name: str = LORE_COLLECTION,
) -> None:
    if len(chunks) != len(embeddings):
        raise ValueError("chunks and embeddings must have the same length")
    if not chunks:
        return

    collection = get_or_create_collection(collection_name)
    collection.upsert(
        ids=[chunk.id for chunk in chunks],
        embeddings=embeddings,
        metadatas=[chunk.chroma_metadata() for chunk in chunks],
        documents=[chunk.text for chunk in chunks],
    )


def query_lore_collection(
    query_embedding: list[float],
    n_results: int = 5,
    where: dict[str, Any] | None = None,
    collection_name: str = LORE_COLLECTION,
) -> dict[str, Any]:
    collection = get_or_create_collection(collection_name)
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where,
    )
