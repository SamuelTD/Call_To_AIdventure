import json
from typing import List, Dict, Any

# A simple, tokenizer-free chunker based on word counts
# This avoids external dependencies on Hugging Face tokenizers.

def chunk_text(text: str, max_words: int = 300) -> List[str]:
    """
    Splits a long string into chunks each containing up to max_words words.
    """
    words = text.split()
    total_words = len(words)
    print(f"[chunk_text] Splitting text of {total_words} words into chunks of up to {max_words} words each...")
    chunks: List[str] = []
    for i in range(0, total_words, max_words):
        chunk = " ".join(words[i:i + max_words])
        chunks.append(chunk)
        print(f"[chunk_text] Created chunk {len(chunks)-1} with {len(chunk.split())} words")
    print(f"[chunk_text] Finished creating {len(chunks)} chunks\n")
    return chunks


def chunk_character_json_file(path: str, max_words: int = 300) -> List[Dict[str, Any]]:
    """
    Reads a JSON world-doc, extracts all relevant text fields,
    and returns a list of chunk dicts with metadata.
    """
    print(f"[chunk_json_file] Processing file: {path}")
    data = json.load(open(path, encoding='utf-8'))
    pieces: List[str] = []

    # 1. Basic identifiers & flavor
    print("[chunk_json_file] Extracting basic fields...")
    for fld in ("name", "title", "race", "age"):
        if data.get(fld):
            pieces.append(str(data[fld]))
            print(f"  - {fld}: {data.get(fld)}")

    # 2. Free-form description
    if data.get("description"):
        pieces.append(data["description"])
        print(f"  - description length: {len(data['description'].split())} words")

    # 3. Background: lineage & notable events
    lineage = data.get("background", {}).get("lineage", [])
    if lineage:
        pieces.extend(lineage)
        print(f"  - lineage entries: {len(lineage)}")
    events = data.get("background", {}).get("notable_events", [])
    if events:
        for evt in events:
            evt_text = evt.get("event", "")
            pieces.append(evt_text)
        print(f"  - notable_events entries: {len(events)}")

    # 4. Personality traits
    traits = data.get("personality_traits", [])
    if traits:
        pieces.extend(traits)
        print(f"  - personality_traits entries: {len(traits)}")

    # 5. Relationships
    rels = data.get("relationships", {})
    if rels.get("allies"):
        allies = ", ".join(rels["allies"])
        pieces.append("Allies: " + allies)
        print(f"  - allies: {allies}")
    if rels.get("enemies"):
        enemies = ", ".join(rels["enemies"])
        pieces.append("Enemies: " + enemies)
        print(f"  - enemies: {enemies}")

    # 6. Location
    if data.get("current_location"):
        location = data["current_location"]
        pieces.append("Location: " + location)
        print(f"  - current_location: {location}")

    # 7. Inventory items
    inventory = data.get("inventory", [])
    if inventory:
        print(f"  - inventory items: {len(inventory)}")
        for item in inventory:
            name = item.get("name", "")
            desc = item.get("description", "")
            pieces.append(f"{name}: {desc}")
            print(f"    · {name}: {len(desc.split())} words")

    # Join all pieces and split into word-based chunks
    full_text = " ".join(pieces)
    print(f"[chunk_json_file] Total concatenated text length: {len(full_text.split())} words")
    text_chunks = chunk_text(full_text, max_words)

    # Build metadata-rich chunk dicts
    chunk_dicts: List[Dict[str, Any]] = []
    for idx, chunk in enumerate(text_chunks):
        metadata = {
            "id": data.get("id", ""),
            "chunk_index": idx,
            "page_content": chunk,
            "type": data.get("type"),
            "tags": data.get("tags", []),
            "source_file": path
        }
        chunk_dicts.append(metadata)
    print(f"[chunk_json_file] Generated {len(chunk_dicts)} metadata entries\n")

    return chunk_dicts

def chunk_location_json_file(path: str, max_words: int = 300) -> List[Dict[str, Any]]:
    """
    Reads a JSON location-doc, extracts all relevant text fields,
    and returns a list of chunk dicts with metadata.
    """
    print(f"[chunk_location_json_file] Processing location file: {path}")
    data = json.load(open(path, encoding='utf-8'))
    pieces: List[str] = []

    # Basic identifiers
    print("[chunk_location_json_file] Extracting basic fields...")
    for fld in ("name", "region", "type"):
        if data.get(fld):
            pieces.append(str(data.get(fld)))
            print(f"  - {fld}: {data.get(fld)}")

    # Description
    if data.get("description"):
        pieces.append(data["description"])
        print(f"  - description length: {len(data['description'].split())} words")

    # History: founding
    founding = data.get("history", {}).get("founding", {})
    if founding:
        line = f"Founded in {founding.get('year')} by {founding.get('founder')} to {founding.get('purpose')}"
        pieces.append(line)
        print(f"  - founding: {line}")
    # History: notable events
    loc_events = data.get("history", {}).get("notable_events", [])
    if loc_events:
        for evt in loc_events:
            text = evt.get("event", "")
            pieces.append(text)
        print(f"  - notable_events entries: {len(loc_events)}")

    # Features
    features = data.get("features", [])
    if features:
        print(f"  - features count: {len(features)}")
        for feat in features:
            name = feat.get("name", "")
            desc = feat.get("description", "")
            pieces.append(f"Feature {name}: {desc}")
            print(f"    · {name}: {len(desc.split())} words")

    # Inhabitants
    inhabitants = data.get("inhabitants", [])
    if inhabitants:
        print(f"  - inhabitants count: {len(inhabitants)}")
        for npc in inhabitants:
            role = npc.get("role", "")
            notes = npc.get("notes", "")
            pieces.append(f"{npc.get('npc_id')}, the {role}: {notes}")
            print(f"    · {npc.get('npc_id')}: {role}")

    # Connections
    conns = data.get("connections", {})
    adj = conns.get("adjacent_locations", [])
    if adj:
        line = "Adjacent: " + ", ".join(adj)
        pieces.append(line)
        print(f"  - adjacent_locations: {adj}")
    secret = conns.get("secret_passages", [])
    if secret:
        for sp in secret:
            method = sp.get("method", "")
            to = sp.get("to", "")
            line = f"Secret to {to}: {method}"
            pieces.append(line)
            print(f"  - secret_passage: {line}")

    # Tags
    tags = data.get("tags", [])
    if tags:
        line = "Tags: " + ", ".join(tags)
        pieces.append(line)
        print(f"  - tags: {tags}")

    # Join and chunk
    full_text = " ".join(pieces)
    print(f"[chunk_location_json_file] Total text length: {len(full_text.split())} words")
    text_chunks = chunk_text(full_text, max_words)

    # Build metadata
    chunk_dicts: List[Dict[str, Any]] = []
    for idx, chunk in enumerate(text_chunks):
        metadata = {
            "id": data.get("id", ""),
            "chunk_index": idx,
            "page_content": chunk,
            "type": data.get("type"),
            "tags": data.get("tags", []),
            "source_file": path
        }
        chunk_dicts.append(metadata)
    print(f"[chunk_location_json_file] Generated {len(chunk_dicts)} location chunks\n")
    return chunk_dicts
