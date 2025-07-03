import json
from typing import List, Dict, Any

# A simple, tokenizer-free chunker based on word counts
# This avoids external dependencies on Hugging Face tokenizers.

def chunk_text(text: str, max_words: int = 300) -> List[str]:
    """
    Splits a long string into chunks each containing up to max_words words.
    """
    words = text.split()
    chunks: List[str] = []
    for i in range(0, len(words), max_words):
        chunks.append(" ".join(words[i:i + max_words]))
    return chunks


def chunk_json_file(path: str, max_words: int = 300) -> List[Dict[str, Any]]:
    """
    Reads a JSON world-doc, extracts all relevant text fields,
    and returns a list of chunk dicts with metadata.
    """
    data = json.load(open(path))
    pieces: List[str] = []

    # 1. Basic identifiers & flavor
    for fld in ("name", "title", "race", "age"):
        if data.get(fld):
            pieces.append(str(data[fld]))

    # 2. Free-form description
    if data.get("description"):
        pieces.append(data["description"])

    # 3. Background: lineage & notable events
    pieces.extend(data.get("background", {}).get("lineage", []))
    pieces.extend(evt.get("event", "") for evt in data.get("background", {}).get("notable_events", []))

    # 4. Personality traits
    pieces.extend(data.get("personality_traits", []))

    # 5. Relationships
    rels = data.get("relationships", {})
    if rels.get("allies"):
        pieces.append("Allies: " + ", ".join(rels["allies"]))
    if rels.get("enemies"):
        pieces.append("Enemies: " + ", ".join(rels["enemies"]))

    # 6. Location
    if data.get("current_location"):
        pieces.append("Location: " + data["current_location"])

    # 7. Inventory items
    for item in data.get("inventory", []):
        name = item.get("name", "")
        desc = item.get("description", "")
        pieces.append(f"{name}: {desc}")

    # Join all pieces and split into word-based chunks
    full_text = " ".join(pieces)
    text_chunks = chunk_text(full_text, max_words)

    # Build metadata-rich chunk dicts
    return [
        {
            "id": data.get("id", ""),
            "chunk_index": idx,
            "page_content": chunk,
            "type": data.get("type"),
            "tags": data.get("tags", []),
            "source_file": path
        }
        for idx, chunk in enumerate(text_chunks)
    ]
