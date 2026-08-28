import hashlib
import json
from pathlib import Path

from retrieval.schemas import (
    CharacterLore,
    ChunkKind,
    EntityType,
    LocationLore,
    LoreChunk,
)


def normalize_lines(lines: list[str | None]) -> list[str]:
    return [line.strip() for line in lines if line and line.strip()]


def join_lines(lines: list[str | None]) -> str:
    return "\n".join(normalize_lines(lines))


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_chunk(
    *,
    entity_type: EntityType,
    entity_id: str,
    entity_name: str,
    chunk_kind: ChunkKind,
    text: str,
    tags: list[str],
    source_path: str,
) -> LoreChunk:
    return LoreChunk(
        id=f"{entity_type}:{entity_id}:{chunk_kind}",
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        chunk_kind=chunk_kind,
        text=text,
        tags=tags,
        source_path=source_path,
        content_hash=content_hash(text),
    )


def character_identity_text(character: CharacterLore) -> str:
    aliases = ", ".join(character.aliases)
    parts = [
        f"Name: {character.name}",
        f"Title: {character.title}" if character.title else None,
        f"Aliases: {aliases}" if aliases else None,
        f"Race: {character.race}" if character.race else None,
        f"Age: {character.age}" if character.age is not None else None,
        f"Current location: {character.current_location}"
        if character.current_location
        else None,
        f"Tags: {', '.join(character.tags)}" if character.tags else None,
    ]
    return join_lines(parts)


def character_history_text(character: CharacterLore) -> str:
    lines: list[str | None] = []
    if character.background.lineage:
        lines.append("Lineage: " + "; ".join(character.background.lineage))

    for event in character.background.notable_events:
        prefix = f"{event.year}: " if event.year is not None else ""
        lines.append(prefix + event.event)

    return join_lines(lines)


def character_relationship_text(character: CharacterLore) -> str:
    relationships = character.relationships
    return join_lines([
        "Allies: " + ", ".join(relationships.allies)
        if relationships.allies
        else None,
        "Enemies: " + ", ".join(relationships.enemies)
        if relationships.enemies
        else None,
    ])


def character_inventory_text(character: CharacterLore) -> str:
    lines = [
        f"{item.name}: {item.description}" if item.description else item.name
        for item in character.inventory
    ]
    return join_lines(lines)


def chunk_character(character: CharacterLore, source_path: str) -> list[LoreChunk]:
    candidates: list[tuple[ChunkKind, str]] = [
        ("identity", character_identity_text(character)),
        ("description", character.description),
        ("personality", join_lines(character.personality_traits)),
        ("relationships", character_relationship_text(character)),
        ("history", character_history_text(character)),
        ("inventory", character_inventory_text(character)),
    ]

    return [
        make_chunk(
            entity_type="character",
            entity_id=character.id,
            entity_name=character.name,
            chunk_kind=chunk_kind,
            text=text,
            tags=character.tags,
            source_path=source_path,
        )
        for chunk_kind, text in candidates
        if text.strip()
    ]


def location_overview_text(location: LocationLore) -> str:
    founding = location.history.founding
    founding_text = None
    if founding:
        founding_bits = normalize_lines([
            str(founding.year) if founding.year is not None else None,
            founding.founder,
            founding.purpose,
        ])
        founding_text = "Founded: " + " | ".join(founding_bits)

    history_events = [
        f"{event.year}: {event.event}" if event.year is not None else event.event
        for event in location.history.notable_events
    ]
    features = [
        f"{feature.name}: {feature.description}"
        if feature.description
        else feature.name
        for feature in location.features
    ]

    return join_lines([
        f"Name: {location.name}",
        f"Region: {location.region}" if location.region else None,
        f"Aliases: {', '.join(location.aliases)}" if location.aliases else None,
        location.description,
        founding_text,
        "History: " + " ".join(history_events) if history_events else None,
        "Features: " + " ".join(features) if features else None,
        f"Tags: {', '.join(location.tags)}" if location.tags else None,
    ])


def location_encounters_text(location: LocationLore) -> str:
    inhabitants = [
        f"{inhabitant.npc_id}"
        f" ({inhabitant.role})"
        f": {inhabitant.notes}"
        for inhabitant in location.inhabitants
    ]
    return join_lines([
        "Monsters: " + ", ".join(location.monsters)
        if location.monsters
        else None,
        "Inhabitants: " + " ".join(inhabitants) if inhabitants else None,
    ])


def location_connections_text(location: LocationLore) -> str:
    secret_passages = [
        f"Secret passage to {passage.to}: {passage.method}"
        for passage in location.connections.secret_passages
    ]
    return join_lines([
        "Adjacent locations: "
        + ", ".join(location.connections.adjacent_locations)
        if location.connections.adjacent_locations
        else None,
        *secret_passages,
    ])


def location_completion_text(location: LocationLore) -> str:
    return join_lines([
        f"Objective: {location.completion.objective}"
        if location.completion.objective
        else None,
        "Signals: " + "; ".join(location.completion.signals)
        if location.completion.signals
        else None,
    ])


def chunk_location(location: LocationLore, source_path: str) -> list[LoreChunk]:
    candidates: list[tuple[ChunkKind, str]] = [
        ("overview", location_overview_text(location)),
        ("encounters", location_encounters_text(location)),
        ("challenges", join_lines(location.challenges)),
        ("connections", location_connections_text(location)),
        ("clues", join_lines(location.clues)),
        ("loot", join_lines(location.loot)),
        ("completion", location_completion_text(location)),
    ]

    return [
        make_chunk(
            entity_type="location",
            entity_id=location.id,
            entity_name=location.name,
            chunk_kind=chunk_kind,
            text=text,
            tags=location.tags,
            source_path=source_path,
        )
        for chunk_kind, text in candidates
        if text.strip()
    ]


def load_character(path: str | Path) -> CharacterLore:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return CharacterLore.model_validate(data)


def load_location(path: str | Path) -> LocationLore:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return LocationLore.model_validate(data)


def chunk_character_json_file(path: str | Path) -> list[LoreChunk]:
    source_path = str(path)
    return chunk_character(load_character(path), source_path)


def chunk_location_json_file(path: str | Path) -> list[LoreChunk]:
    source_path = str(path)
    return chunk_location(load_location(path), source_path)
