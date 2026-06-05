from typing import Any

from retrieval.client import query_lore_collection
from retrieval.embedder import embed
from retrieval.schemas import (
    EntityType,
    LoreChunk,
    LoreChunkResult,
    RagContext,
    RetrievalScope,
)
from utils.adventure import Adventure


def build_retrieval_scope(
    adventure: Adventure,
    *,
    current_location_id: str | None = None,
) -> RetrievalScope:
    return RetrievalScope(
        active_character_ids=adventure.characters.active,
        referenceable_character_ids=adventure.characters.referenceable,
        available_location_ids=adventure.locations.available,
        current_location_id=current_location_id or adventure.locations.start,
    )


def scoped_entity_ids(
    scope: RetrievalScope,
    entity_type: EntityType,
) -> list[str]:
    if entity_type == "character":
        return scope.allowed_character_ids
    return scope.allowed_location_ids


def has_retrievable_scope(
    scope: RetrievalScope,
    entity_types: list[EntityType] | None = None,
) -> bool:
    requested_types = entity_types or ["character", "location"]
    return any(scoped_entity_ids(scope, entity_type) for entity_type in requested_types)


def build_scope_filter(
    scope: RetrievalScope,
    entity_types: list[EntityType] | None = None,
) -> dict[str, Any] | None:
    requested_types = entity_types or ["character", "location"]
    clauses: list[dict[str, Any]] = []

    for entity_type in requested_types:
        entity_ids = scoped_entity_ids(scope, entity_type)
        if not entity_ids:
            continue
        clauses.append({
            "$and": [
                {"entity_type": entity_type},
                {"entity_id": {"$in": entity_ids}},
            ]
        })

    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$or": clauses}


def parse_tags(value: Any) -> list[str]:
    if isinstance(value, str):
        return [tag.strip() for tag in value.split(",") if tag.strip()]
    if isinstance(value, list):
        return [str(tag) for tag in value if str(tag).strip()]
    return []


def chunk_from_chroma_result(
    *,
    chunk_id: str,
    document: str,
    metadata: dict[str, Any],
) -> LoreChunk:
    return LoreChunk(
        id=chunk_id,
        entity_type=metadata["entity_type"],
        entity_id=metadata["entity_id"],
        entity_name=metadata["entity_name"],
        chunk_kind=metadata["chunk_kind"],
        text=document,
        tags=parse_tags(metadata.get("tags")),
        source_path=metadata["source_path"],
        schema_version=int(metadata.get("schema_version", 1)),
        content_hash=metadata["content_hash"],
    )


def rag_context_from_chroma_results(results: dict[str, Any]) -> RagContext:
    ids = (results.get("ids") or [[]])[0]
    documents = (results.get("documents") or [[]])[0]
    metadatas = (results.get("metadatas") or [[]])[0]
    distances = (results.get("distances") or [[]])[0]

    chunk_results: list[LoreChunkResult] = []
    for index, chunk_id in enumerate(ids):
        chunk = chunk_from_chroma_result(
            chunk_id=chunk_id,
            document=documents[index],
            metadata=metadatas[index],
        )
        distance = distances[index] if index < len(distances) else None
        chunk_results.append(LoreChunkResult(chunk=chunk, distance=distance))

    return RagContext(chunks=chunk_results)


def retrieve_lore_context(
    query: str,
    scope: RetrievalScope,
    *,
    entity_types: list[EntityType] | None = None,
    top_k: int = 5,
) -> RagContext:
    if not query.strip():
        return RagContext()
    if not has_retrievable_scope(scope, entity_types):
        return RagContext()

    where = build_scope_filter(scope, entity_types)
    query_embedding = embed(query)
    results = query_lore_collection(
        query_embedding=query_embedding,
        n_results=top_k,
        where=where,
    )
    return rag_context_from_chroma_results(results)
