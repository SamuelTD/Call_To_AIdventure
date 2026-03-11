from typing import List, Dict, Any, Optional
import chromadb
from utils.pathing import CHROMA_DIR
from chromadb.api.models.Collection import Collection
from chromadb.errors import NotFoundError

client = chromadb.PersistentClient(path=str(CHROMA_DIR))

def get_or_create_collection(name: str) -> Collection:
    """
    Retrieve an existing ChromaDB collection by name, or create it if it doesn’t exist.
    """
    try:
        return client.get_collection(name)
    except NotFoundError:
        return client.create_collection(name=name)


def upsert_chunks(
    collection_name: str,
    embeddings: List[List[float]],
    chunks: List[Dict[str, Any]]
) -> None:
    """
    Upsert chunk embeddings and their associated metadata into the specified collection.

    Args:
        collection_name: Name of the ChromaDB collection.
        embeddings: List of embedding vectors, one per chunk.
        chunks: List of dicts containing chunk metadata and text.
    """
    col = get_or_create_collection(collection_name)

    ids = [f"{c['id']}_{c['chunk_index']}" for c in chunks]
    metadatas: List[Dict[str, Any]] = []
    for c in chunks:
        # Convert tags list to comma-separated string for metadata compliance
        tags_value = c.get('tags')
        metadata_entry = {
            'id': c['id'],
            'type': c.get('type'),
            'tags': ','.join(tags_value) if isinstance(tags_value, list) else None,
            'source_file': c.get('source_file'),
            'chunk_index': c.get('chunk_index'),
        }
        metadatas.append(metadata_entry)

    documents = [c['page_content'] for c in chunks]

    col.upsert(
        ids=ids,
        embeddings=embeddings,
        metadatas=metadatas,
        documents=documents,
    )


def query_collection(
    collection_name: str,
    query_embedding: List[float],
    n_results: int = 5,
    where: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Query the collection for the most semantically similar chunks.

    Args:
        collection_name: Name of the ChromaDB collection.
        query_embedding: Embedding vector of the user's input.
        n_results: Number of nearest neighbors to retrieve.
        where: Optional metadata filter, e.g., {'type': 'character'}.

    Returns:
        A dict with keys: 'ids', 'distances', 'metadatas', 'documents'.
    """
    col = get_or_create_collection(collection_name)
    results = col.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where,
    )
    return results
