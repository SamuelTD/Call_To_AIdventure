from typing import Any, Literal

from pydantic import BaseModel, Field


EntityType = Literal["character", "location"]
CharacterChunkKind = Literal[
    "identity",
    "description",
    "personality",
    "relationships",
    "history",
    "inventory",
]
LocationChunkKind = Literal[
    "overview",
    "encounters",
    "challenges",
    "connections",
    "clues",
    "loot",
]
ChunkKind = CharacterChunkKind | LocationChunkKind
Visibility = Literal["active", "referenceable", "global"]


class NotableEvent(BaseModel):
    year: int | str | None = None
    event: str


class CharacterBackground(BaseModel):
    lineage: list[str] = Field(default_factory=list)
    notable_events: list[NotableEvent] = Field(default_factory=list)


class CharacterRelationships(BaseModel):
    allies: list[str] = Field(default_factory=list)
    enemies: list[str] = Field(default_factory=list)


class CharacterInventoryItem(BaseModel):
    item_id: str | None = None
    name: str
    description: str = ""


class CharacterLore(BaseModel):
    id: str
    type: Literal["character"] = "character"
    name: str
    aliases: list[str] = Field(default_factory=list)
    title: str | None = None
    age: int | str | None = None
    race: str | None = None
    description: str = ""
    background: CharacterBackground = Field(default_factory=CharacterBackground)
    personality_traits: list[str] = Field(default_factory=list)
    relationships: CharacterRelationships = Field(
        default_factory=CharacterRelationships
    )
    current_location: str | None = None
    inventory: list[CharacterInventoryItem] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class LocationFounding(BaseModel):
    year: int | str | None = None
    founder: str | None = None
    purpose: str | None = None


class LocationHistory(BaseModel):
    founding: LocationFounding | None = None
    notable_events: list[NotableEvent] = Field(default_factory=list)


class LocationFeature(BaseModel):
    feature_id: str | None = None
    name: str
    description: str = ""


class LocationInhabitant(BaseModel):
    npc_id: str
    role: str = ""
    notes: str = ""


class SecretPassage(BaseModel):
    to: str
    method: str = ""


class LocationConnections(BaseModel):
    adjacent_locations: list[str] = Field(default_factory=list)
    secret_passages: list[SecretPassage] = Field(default_factory=list)


class LocationLore(BaseModel):
    id: str
    type: Literal["location"] = "location"
    name: str
    aliases: list[str] = Field(default_factory=list)
    region: str | None = None
    description: str = ""
    monsters: list[str] = Field(default_factory=list)
    challenges: list[str] = Field(default_factory=list)
    clues: list[str] = Field(default_factory=list)
    loot: list[str] = Field(default_factory=list)
    history: LocationHistory = Field(default_factory=LocationHistory)
    features: list[LocationFeature] = Field(default_factory=list)
    inhabitants: list[LocationInhabitant] = Field(default_factory=list)
    connections: LocationConnections = Field(default_factory=LocationConnections)
    tags: list[str] = Field(default_factory=list)


class LoreChunk(BaseModel):
    id: str
    entity_type: EntityType
    entity_id: str
    entity_name: str
    chunk_kind: ChunkKind
    text: str
    tags: list[str] = Field(default_factory=list)
    source_path: str
    schema_version: int = 1
    content_hash: str

    def chroma_metadata(self) -> dict[str, Any]:
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "chunk_kind": self.chunk_kind,
            "tags": ",".join(self.tags),
            "source_path": self.source_path,
            "schema_version": self.schema_version,
            "content_hash": self.content_hash,
        }


class LoreChunkResult(BaseModel):
    chunk: LoreChunk
    distance: float | None = None


class RetrievalScope(BaseModel):
    active_character_ids: list[str] = Field(default_factory=list)
    referenceable_character_ids: list[str] = Field(default_factory=list)
    available_location_ids: list[str] = Field(default_factory=list)
    current_location_id: str | None = None

    @property
    def allowed_character_ids(self) -> list[str]:
        return list(dict.fromkeys([
            *self.active_character_ids,
            *self.referenceable_character_ids,
        ]))

    @property
    def allowed_location_ids(self) -> list[str]:
        return list(dict.fromkeys([
            *(
                [self.current_location_id]
                if self.current_location_id is not None
                else []
            ),
            *self.available_location_ids,
        ]))


class RagContext(BaseModel):
    chunks: list[LoreChunkResult] = Field(default_factory=list)

    def format_for_prompt(self) -> str:
        if not self.chunks:
            return "No relevant world lore was retrieved."

        lines: list[str] = []
        for result in self.chunks:
            chunk = result.chunk
            lines.append(
                f"- [{chunk.entity_type}:{chunk.entity_id}:{chunk.chunk_kind}] "
                f"{chunk.text}"
            )
        return "\n".join(lines)
