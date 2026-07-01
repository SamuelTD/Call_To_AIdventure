# RAG System Documentation

This document describes the current Retrieval-Augmented Generation system in
Call_To_AIdventure as it exists in the codebase.

The RAG system lives under `src/retrieval/` and is used by the active LangGraph
game master in `src/agents/game_master_graph.py`. It has two main jobs:

1. Build a local vector database from structured world lore JSON files.
2. Retrieve relevant, adventure-scoped lore at runtime and inject it into LLM
   prompts for story generation, combat narration, and choice generation.

## Current Status

The RAG system is implemented and called from the active game graph.

It currently indexes:

- character lore from `data/world/characters/*.json`
- location lore from `data/world/locations/*.json`

It stores vectors in a persistent ChromaDB database at:

```text
db/chroma/
```

The default Chroma collection is:

```text
world_lore
```

The current dry-run ingestion prepares 39 chunks:

- 6 chunks for each of 6 character files
- 3 chunks for `ravenhold_grand_library.json`

RAG is scoped by the selected adventure. At the moment, the shipped adventures
mostly reference `king_eoric` as a referenceable character and do not list
available locations, so runtime retrieval is useful but narrow. Location
retrieval will become more important when adventure JSON files populate
`locations.available` and/or `locations.start`.

## High-Level Architecture

```text
World JSON files
      |
      v
src/retrieval/chunker.py
      |
      v
LoreChunk objects
      |
      v
src/retrieval/embedder.py  -> Ollama OpenAI-compatible embeddings endpoint
      |
      v
src/retrieval/client.py    -> Chroma PersistentClient
      |
      v
db/chroma/world_lore

Runtime game graph
      |
      v
src/retrieval/service.py
      |
      v
Scoped Chroma query
      |
      v
RagContext.format_for_prompt()
      |
      v
Story, combat, and choice prompts
```

## Modules

### `src/retrieval/schemas.py`

This file defines the typed data structures used by the RAG system.

World lore schemas:

- `CharacterLore`
- `LocationLore`

Chunk and retrieval schemas:

- `LoreChunk`
- `LoreChunkResult`
- `RetrievalScope`
- `RagContext`

Important type aliases:

- `EntityType`: `"character"` or `"location"`
- `ChunkKind`: one of the supported character or location chunk kinds
- `Visibility`: defined as `"active"`, `"referenceable"`, or `"global"`, but
  not currently used by the retrieval flow

`LoreChunk` is the central storage unit. It contains:

- `id`: stable chunk id, formatted like `character:king_eoric:identity`
- `entity_type`: `character` or `location`
- `entity_id`: source entity id from JSON
- `entity_name`: human-readable entity name
- `chunk_kind`: semantic chunk category
- `text`: text sent to the embedding model and later shown to the LLM
- `tags`: source tags
- `source_path`: source JSON file
- `schema_version`: currently `1`
- `content_hash`: SHA-256 hash of the chunk text

`LoreChunk.chroma_metadata()` converts the chunk into Chroma metadata. Tags are
stored as a comma-separated string because Chroma metadata values need to be
simple scalar values.

`RetrievalScope` controls which indexed entities are allowed at runtime. It has:

- `active_character_ids`
- `referenceable_character_ids`
- `available_location_ids`
- `current_location_id`

It also exposes:

- `allowed_character_ids`: active plus referenceable characters, deduplicated
- `allowed_location_ids`: current location first, then available locations,
  deduplicated

`RagContext.format_for_prompt()` converts retrieval results into prompt text.
When no chunks are retrieved, it returns:

```text
No relevant world lore was retrieved.
```

When chunks are present, each line looks like:

```text
- [character:king_eoric:identity] Name: King Eoric
...
```

### `src/retrieval/chunker.py`

This file converts structured character and location JSON into semantically
named chunks.

Shared helpers:

- `normalize_lines()`: strips empty lines
- `join_lines()`: joins non-empty lines with newlines
- `content_hash()`: creates a SHA-256 hash of chunk text
- `make_chunk()`: builds a `LoreChunk` with a stable id

Character chunk kinds:

- `identity`
- `description`
- `personality`
- `relationships`
- `history`
- `inventory`

Each character JSON file can therefore produce up to 6 chunks. The current
character files all produce 6 chunks.

Location chunk kinds:

- `overview`
- `encounters`
- `challenges`
- `connections`
- `clues`
- `loot`

Location files produce only the chunks that have non-empty text. The current
`ravenhold_grand_library.json` file produces 3 chunks because only overview,
encounters, and connections contain data.

The public file-level chunking functions are:

```python
chunk_character_json_file(path)
chunk_location_json_file(path)
```

Both functions parse JSON through Pydantic models before chunking, so malformed
world lore should fail early.

### `src/retrieval/embedder.py`

This file embeds text through Ollama.

Environment variables:

- `OLLAMA_HOST`, default `http://localhost:11434`
- `EMBED_MODEL`, default `mxbai-embed-large:latest`

The active `embed(text)` function sends a direct HTTP request to:

```text
{OLLAMA_HOST}/v1/embeddings
```

Payload:

```json
{
  "model": "mxbai-embed-large:latest",
  "input": ["text to embed"]
}
```

It expects an OpenAI-compatible response with:

```json
{
  "data": [
    {
      "embedding": [...]
    }
  ]
}
```

The file also creates `ollama_embeddings = OllamaEmbeddings(model=EMBED_MODEL)`,
but the current ingestion and retrieval paths use the direct `requests.post()`
implementation instead of that LangChain object.

### `src/retrieval/client.py`

This file owns ChromaDB access.

It creates a persistent client:

```python
client = chromadb.PersistentClient(path=str(CHROMA_DIR))
```

`CHROMA_DIR` is defined in `src/utils/pathing.py` as:

```text
<project-root>/db/chroma
```

The default collection name is:

```python
LORE_COLLECTION = "world_lore"
```

Public functions:

- `get_or_create_collection(name=LORE_COLLECTION)`
- `reset_collection(name=LORE_COLLECTION)`
- `upsert_lore_chunks(chunks, embeddings, collection_name=LORE_COLLECTION)`
- `query_lore_collection(query_embedding, n_results=5, where=None, collection_name=LORE_COLLECTION)`

`upsert_lore_chunks()` writes:

- chunk ids as Chroma ids
- embedding vectors as Chroma embeddings
- `LoreChunk.chroma_metadata()` output as metadata
- chunk text as Chroma documents

`query_lore_collection()` runs a vector query and accepts an optional Chroma
`where` filter. Runtime retrieval always uses this filter to keep lore inside
the current adventure scope.

### `src/retrieval/ingest.py`

This file is the command-line ingestion entry point.

Default source directories:

```text
data/world/characters
data/world/locations
```

Default target collection:

```text
world_lore
```

Common commands:

```bash
uv run python -m retrieval.ingest --dry-run
uv run python -m retrieval.ingest --reset
```

Flags:

- `--characters`: ingest only character files
- `--locations`: ingest only location files
- `--character-dir PATH`: override character source directory
- `--location-dir PATH`: override location source directory
- `--collection NAME`: override Chroma collection name
- `--reset`: delete the target collection before ingesting
- `--dry-run`: chunk files but do not call Ollama and do not write to Chroma

Default behavior:

- If neither `--characters` nor `--locations` is passed, both are ingested.
- If `--characters` is passed, only character files are ingested.
- If `--locations` is passed, only location files are ingested.
- `--reset` is ignored during `--dry-run`.

The ingestion flow is:

1. Find JSON files in the selected source directories.
2. Convert each file into `LoreChunk` objects.
3. If `--dry-run` is active, print the number of chunks and stop.
4. If `--reset` is active, delete the target Chroma collection.
5. Embed each chunk through Ollama.
6. Upsert chunks, metadata, documents, and embeddings into Chroma.

### `src/retrieval/service.py`

This file is the runtime retrieval API used by the game graph.

Important functions:

- `build_retrieval_scope(adventure, current_location_id=None)`
- `build_scope_filter(scope, entity_types=None)`
- `retrieve_lore_context(query, scope, entity_types=None, top_k=5)`

`build_retrieval_scope()` derives a `RetrievalScope` from the loaded adventure:

```python
RetrievalScope(
    active_character_ids=adventure.characters.active,
    referenceable_character_ids=adventure.characters.referenceable,
    available_location_ids=adventure.locations.available,
    current_location_id=current_location_id or adventure.locations.start,
)
```

`build_scope_filter()` builds Chroma metadata filters. For example, an adventure
that allows `king_eoric` and starts in `ravenhold_grand_library` would produce a
filter shaped like:

```python
{
    "$or": [
        {
            "$and": [
                {"entity_type": "character"},
                {"entity_id": {"$in": ["king_eoric"]}},
            ]
        },
        {
            "$and": [
                {"entity_type": "location"},
                {"entity_id": {"$in": ["ravenhold_grand_library"]}},
            ]
        },
    ]
}
```

`retrieve_lore_context()`:

1. Returns an empty `RagContext` if the query is blank.
2. Returns an empty `RagContext` if the scope has no allowed ids.
3. Embeds the query through Ollama.
4. Queries Chroma with the scope filter.
5. Converts Chroma results back into `LoreChunk` objects.
6. Returns a `RagContext`.

## Runtime Integration

Runtime integration happens in `src/agents/game_master_graph.py`.

The graph imports:

```python
from retrieval.schemas import EntityType, RagContext
from retrieval.service import build_retrieval_scope, retrieve_lore_context
```

The graph wrapper is:

```python
retrieve_rag_context(state, query, entity_types=None, top_k=5)
```

It:

1. Builds a retrieval scope from `state["adventure"]`.
2. Uses `state.get("current_location_id")` when available.
3. Calls `retrieve_lore_context()`.
4. Formats results with `RagContext.format_for_prompt()`.
5. Catches any retrieval exception and falls back to the empty-lore message.

This means RAG failures should not crash the game loop. If Ollama, Chroma, or
embedding retrieval fails, the graph logs `ERROR RAG RETRIEVAL:` and continues
without retrieved lore.

RAG context is used in three runtime places.

### Choice Generation

Function:

```python
step_get_input()
```

Query shape:

```text
<current story>
What can the player do next?
```

Top K:

```text
4
```

The retrieved lore is passed into `make_choice()`, which invokes
`CHOOSER_TEMPLATE` from `src/agents/prompts/chooser.py`.

The chooser prompt explicitly tells the model:

- use retrieved lore only when relevant
- do not offer actions involving characters or locations outside the current
  adventure scope
- return exactly three possible next actions

### Pre-Combat Narration

Function:

```python
step_prepare_combat()
```

Query shape:

```text
<current story>
<latest user input>
<current monster name>
```

Top K:

```text
3
```

The retrieved lore is passed into `build_pre_combat_fluff_prompt()`.

### Story Continuation

Function:

```python
step_generate_story()
```

Query shape:

```text
<current story>
<latest user input>
```

Top K:

```text
5
```

The retrieved lore is passed into different story prompts depending on the last
command:

- `build_regular_story_prompt()`
- `build_post_combat_story_prompt()`
- `build_post_heal_story_prompt()`
- `build_post_damage_story_prompt()`

All of these prompts include the shared lore section from
`src/agents/prompts/story.py`:

```text
Relevant world lore:
<retrieved lore>

Lore rules:
- Use retrieved lore only when it is relevant to the current scene.
- Do not introduce characters or locations outside the current adventure scope.
- Current game state and resolved narrative override retrieved lore.
```

## Adventure Scope Configuration

Adventure JSON files define which lore can be retrieved.

Relevant fields:

```json
{
  "characters": {
    "active": [],
    "referenceable": ["king_eoric"]
  },
  "locations": {
    "available": [],
    "start": null
  }
}
```

Character behavior:

- `active` characters are eligible for retrieval.
- `referenceable` characters are also eligible for retrieval.
- Both lists are combined into `allowed_character_ids`.

Location behavior:

- `locations.start` becomes the current location when no runtime
  `current_location_id` is present.
- `locations.available` is also eligible for retrieval.
- Both are combined into `allowed_location_ids`.

Current shipped adventure examples:

- `emerald_sword` references `king_eoric`.
- `l_epee_d_emeraude` references `king_eoric`.
- `test_adv` has no scoped characters or locations.

Because `emerald_sword` and `l_epee_d_emeraude` do not define available or start
locations, their runtime RAG scope currently only permits King Eoric character
lore.

## Data Contracts

### Character JSON

Character files must match `CharacterLore`.

Important fields:

- `id`
- `type`, normally `"character"`
- `name`
- `aliases`
- `title`
- `age`
- `race`
- `description`
- `background.lineage`
- `background.notable_events`
- `personality_traits`
- `relationships.allies`
- `relationships.enemies`
- `current_location`
- `inventory`
- `tags`

### Location JSON

Location files must match `LocationLore`.

Important fields:

- `id`
- `type`, normally `"location"`
- `name`
- `aliases`
- `region`
- `description`
- `monsters`
- `challenges`
- `clues`
- `loot`
- `history.founding`
- `history.notable_events`
- `features`
- `inhabitants`
- `connections.adjacent_locations`
- `connections.secret_passages`
- `tags`

### Chroma Metadata

Each chunk stores this metadata:

```python
{
    "entity_type": "character",
    "entity_id": "king_eoric",
    "entity_name": "King Eoric",
    "chunk_kind": "identity",
    "tags": "monarch,noble,stoic",
    "source_path": ".../data/world/characters/king_eoric.json",
    "schema_version": 1,
    "content_hash": "...",
}
```

This metadata is what makes adventure-scoped retrieval possible.

## Setup and Operation

1. Make sure Ollama is running.

2. Pull the embedding model.

```bash
ollama pull mxbai-embed-large:latest
```

3. Configure `.env` if needed.

```bash
OLLAMA_HOST=http://localhost:11434
EMBED_MODEL=mxbai-embed-large:latest
```

4. Validate chunking without embedding.

```bash
uv run python -m retrieval.ingest --dry-run
```

5. Rebuild the Chroma collection.

```bash
uv run python -m retrieval.ingest --reset
```

6. Run the Django app normally.

```bash
uv run python src/django/manage.py runserver
```

During gameplay, the graph will retrieve lore automatically before relevant LLM
calls.

## Current Limitations

- Runtime retrieval depends on Ollama being reachable. If Ollama is down,
  retrieval fails and the game falls back to "No relevant world lore was
  retrieved."
- `current_location_id` exists in `GameState`, but the current graph does not
  visibly update it as the story moves. Location-aware retrieval is therefore
  mostly driven by the adventure's configured start and available locations.
- The shipped playable adventures currently do not list available/start
  locations, so location lore is indexed but generally not reachable from those
  adventures.
- The RAG corpus does not currently include adventure intro/outro text, monster
  data, items, or general documents under `data/documents/`.
- Chunking is schema-based and hand-authored. There is no automatic text
  splitter for arbitrary prose documents.
- `Visibility` is defined in schemas but not currently used.
- `content_hash` is stored but not used to skip unchanged chunks. Ingestion
  upserts all generated chunks.
- `tags` are stored as comma-separated metadata, but runtime filters do not
  currently filter on tags.
- The `OllamaEmbeddings` object in `embedder.py` is currently unused by the main
  ingestion and retrieval paths.
- RAG retrieval is not used by goal evaluation or victory wrap-up prompts.

## Extending the RAG System

To add more character lore:

1. Add a JSON file under `data/world/characters/`.
2. Make sure the file validates against `CharacterLore`.
3. Add the character id to an adventure's `characters.active` or
   `characters.referenceable`.
4. Re-run ingestion.

To add more location lore:

1. Add a JSON file under `data/world/locations/`.
2. Make sure the file validates against `LocationLore`.
3. Add the location id to an adventure's `locations.start` or
   `locations.available`.
4. Re-run ingestion.

To add a new chunk kind:

1. Update the relevant `ChunkKind` type in `schemas.py`.
2. Add text-building logic in `chunker.py`.
3. Ensure the produced chunk has stable text and a stable id.
4. Re-run `uv run python -m retrieval.ingest --dry-run`.
5. Rebuild the Chroma collection.

To retrieve a narrower entity type at runtime, pass `entity_types`:

```python
retrieve_rag_context(
    state,
    query,
    entity_types=["character"],
    top_k=3,
)
```

The service layer already supports this, although the current graph mostly
retrieves both characters and locations.

## Troubleshooting

If ingestion fails with an Ollama connection error:

- confirm Ollama is running
- confirm `OLLAMA_HOST`
- confirm the embedding model is pulled

If dry-run works but runtime retrieval returns no lore:

- check that the relevant entity JSON was ingested
- check that the selected adventure includes the entity id in its scope
- check that `locations.start` or `locations.available` is set for location lore
- rebuild Chroma with `uv run python -m retrieval.ingest --reset`

If Django gameplay works but retrieved lore is always empty:

- confirm `db/chroma/` exists and contains the `world_lore` collection
- confirm the same `EMBED_MODEL` is used for ingestion and query embeddings
- check logs for `ERROR RAG RETRIEVAL:`

If a module import fails when running retrieval scripts directly:

- run commands from the repository root
- prefer `uv run python -m retrieval.ingest ...`
- if your shell setup requires it, set `PYTHONPATH=src`

## Files at a Glance

```text
src/retrieval/schemas.py      Pydantic schemas and prompt formatting
src/retrieval/chunker.py      JSON-to-LoreChunk conversion
src/retrieval/embedder.py     Ollama embedding request
src/retrieval/client.py       Persistent Chroma client
src/retrieval/ingest.py       CLI ingestion script
src/retrieval/service.py      Runtime scoped retrieval
src/agents/game_master_graph.py
                              Runtime graph integration
src/agents/prompts/story.py   Story prompt lore section
src/agents/prompts/chooser.py Choice prompt lore section
data/world/characters/        Character source lore
data/world/locations/         Location source lore
db/chroma/                    Local Chroma persistence directory
```
