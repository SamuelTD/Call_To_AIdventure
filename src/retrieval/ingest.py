import argparse
from collections.abc import Callable
from pathlib import Path

from retrieval.chunker import chunk_character_json_file, chunk_location_json_file
from retrieval.client import LORE_COLLECTION, reset_collection, upsert_lore_chunks
from retrieval.embedder import embed
from retrieval.schemas import LoreChunk
from utils.pathing import project_path


DEFAULT_CHARACTER_DIR = project_path("data/world/characters")
DEFAULT_LOCATION_DIR = project_path("data/world/locations")


def iter_json_files(path: Path) -> list[Path]:
    if not path.exists():
        raise FileNotFoundError(f"Directory does not exist: {path}")
    return sorted(file for file in path.glob("*.json") if file.is_file())


def build_chunks(
    path: Path,
    chunk_file: Callable[[Path], list[LoreChunk]],
) -> list[LoreChunk]:
    chunks: list[LoreChunk] = []
    for file_path in iter_json_files(path):
        file_chunks = chunk_file(file_path)
        chunks.extend(file_chunks)
        print(f"{file_path}: {len(file_chunks)} chunks")
    return chunks


def embed_chunks(chunks: list[LoreChunk]) -> list[list[float]]:
    embeddings: list[list[float]] = []
    for index, chunk in enumerate(chunks, start=1):
        print(f"Embedding {index}/{len(chunks)}: {chunk.id}")
        embeddings.append(embed(chunk.text))
    return embeddings


def ingest_chunks(
    chunks: list[LoreChunk],
    *,
    collection_name: str,
    dry_run: bool,
) -> None:
    if dry_run:
        print(f"Dry run: would upsert {len(chunks)} chunks into {collection_name}")
        return

    embeddings = embed_chunks(chunks)
    upsert_lore_chunks(chunks, embeddings, collection_name=collection_name)
    print(f"Upserted {len(chunks)} chunks into {collection_name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest character and location lore into the RAG store."
    )
    parser.add_argument(
        "--characters",
        action="store_true",
        help="Ingest character sheets.",
    )
    parser.add_argument(
        "--locations",
        action="store_true",
        help="Ingest location sheets.",
    )
    parser.add_argument(
        "--character-dir",
        type=Path,
        default=DEFAULT_CHARACTER_DIR,
        help="Directory containing character JSON files.",
    )
    parser.add_argument(
        "--location-dir",
        type=Path,
        default=DEFAULT_LOCATION_DIR,
        help="Directory containing location JSON files.",
    )
    parser.add_argument(
        "--collection",
        default=LORE_COLLECTION,
        help="Chroma collection name.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the target collection before ingesting.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and chunk files without embedding or upserting.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ingest_characters = args.characters or not args.locations
    ingest_locations = args.locations or not args.characters

    chunks: list[LoreChunk] = []
    if ingest_characters:
        chunks.extend(build_chunks(args.character_dir, chunk_character_json_file))
    if ingest_locations:
        chunks.extend(build_chunks(args.location_dir, chunk_location_json_file))

    print(f"Prepared {len(chunks)} total chunks")

    if args.reset and not args.dry_run:
        reset_collection(args.collection)
        print(f"Reset collection {args.collection}")

    ingest_chunks(chunks, collection_name=args.collection, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
