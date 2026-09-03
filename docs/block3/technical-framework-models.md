# Block 3 technical framework models

## Architecture scope

The active application is a Django web app integrating an AI game-master
workflow. Django owns user-facing pages, sessions, authentication and JSON
endpoints. `GameEngine` owns the boundary to LangGraph and deterministic
combat. Retrieval and LLM provider calls are internal services behind the graph.

Legacy Gradio files are not part of the active browser production surface.

## C4 context

```mermaid
flowchart LR
    Player[Player / evaluator] --> Browser[Web browser]
    Browser --> Django[Django web application]
    Django --> AppDB[(Django SQLite DB)]
    Django --> DataDB[(Read-only game data SQLite DB)]
    Django --> GameEngine[GameEngine service adapter]
    GameEngine --> LangGraph[LangGraph AI workflow]
    LangGraph --> Retrieval[RAG retrieval service]
    Retrieval --> Chroma[(ChromaDB collection)]
    LangGraph --> OpenAI[OpenAI-compatible generation provider]
    Retrieval --> Ollama[Local Ollama embeddings]
    Prometheus[Prometheus] --> Django
    Grafana[Grafana] --> Prometheus
```

## Container/component model

```mermaid
flowchart TB
    subgraph DjangoProject[src/django/call_to_aidventure]
        Settings[settings.py]
        RootUrls[urls.py]
    end

    subgraph GameApp[src/django/game]
        Views[views.py]
        Templates[templates]
        Models[models.py]
        GameServices[services/tools.py]
        EngineAdapter[services/game_engine.py]
        Tests[tests.py]
    end

    subgraph Domain[src]
        Combat[combat/core.py]
        Agents[agents/game_master_graph.py]
        Retrieval[retrieval/service.py]
        Utils[utils/player.py utils/adventure.py utils/monster.py]
        Metrics[observability/metrics.py]
    end

    Browser[Browser] --> Templates
    Templates --> Views
    Views --> GameServices
    Views --> EngineAdapter
    Views --> Models
    Views --> Metrics
    EngineAdapter --> Combat
    EngineAdapter --> Agents
    Agents --> Retrieval
    GameServices --> Utils
```

## Data ownership

| Data | Owner module | Storage | Lifecycle |
|---|---|---|---|
| Django users | `django.contrib.auth` | Django DB | Created by signup/admin, deleted by user/admin tooling |
| Sessions | Django session framework | Django DB by default | Created per browser session, expires by Django settings |
| Active anonymous game state | `game.services.tools.persist_game` | Session only | Lost when session expires/clears |
| Authenticated save state | `SaveGame` | Django DB JSON field | Created on new game, updated on turn, marked finished on ending |
| Character templates | `CharacterTemplate` | Django DB | Created/updated/deleted by owner; generic templates seeded |
| Adventure metadata | `utils.adventure` | Read-only dataset DB/files | Loaded at runtime; changed by data pipeline |
| Monster data | `utils.monster` | Read-only dataset DB | Loaded at combat start |
| RAG chunks | `retrieval` | ChromaDB collection | Built/updated by ingest process |
| Metrics | `observability.metrics` | Prometheus scrape store | Retained by Prometheus config |

## Entity relationship model

```mermaid
erDiagram
    USER ||--o{ SAVE_GAME : owns
    USER ||--o{ CHARACTER_TEMPLATE : owns
    USER ||--o{ SESSION : has

    USER {
        int id PK
        string username
        string password_hash
        bool is_active
        datetime date_joined
    }

    SAVE_GAME {
        int id PK
        int user_id FK
        string adventure_id
        string adventure_name
        json state
        bool is_finished
        datetime finished_at
        datetime created_at
        datetime updated_at
    }

    CHARACTER_TEMPLATE {
        int id PK
        int user_id FK
        string name
        string race
        string character_class
        string gender
        datetime created_at
        datetime updated_at
    }

    SESSION {
        string session_key PK
        json session_data
        datetime expire_date
    }
```

External read-only data is intentionally modeled separately from the Django DB:

```mermaid
erDiagram
    ADVENTURE ||--o{ LOCATION : references
    ADVENTURE ||--o{ MONSTER : references
    ADVENTURE ||--o{ CHARACTER : references

    ADVENTURE {
        string id PK
        string name
        string description
        json goals
    }

    MONSTER {
        string name PK
        int hp
        int armor
        int strength
        json items_loot
        int gold_loot_min
        int gold_loot_max
    }

    LOCATION {
        string id PK
        string name
        json exits
        text description
    }

    CHARACTER {
        string id PK
        string name
        text description
    }
```

## Target deployment model

```mermaid
flowchart LR
    User[Browser] --> Proxy[HTTPS reverse proxy]
    Proxy --> Web[Django app container]
    Web --> AppDB[(Application database)]
    Web --> Static[Static files]
    Web --> DataDB[(Read-only game dataset)]
    Web --> Chroma[(ChromaDB)]
    Web --> AIProvider[OpenAI-compatible API]
    Web --> Ollama[Embedding service]
    Prometheus --> Web
    Alertmanager --> Operator[Operator notification]
    Grafana --> Prometheus
```

## Environment matrix

| Concern | Development | Test/CI | Target deployment |
|---|---|---|---|
| `DJANGO_DEBUG` | `true` | `false` where deploy checks run | `false` |
| `DJANGO_SECRET_KEY` | Optional dev fallback | Required test value | Required secret manager value |
| `DJANGO_ALLOWED_HOSTS` | localhost defaults | explicit test host | production domains |
| Database | SQLite local | SQLite disposable | selected managed DB or mounted SQLite only for demo |
| Static files | Django dev server | collected/built artifact | served by app/proxy/object storage |
| AI key | optional for mocked tests | secret only for live eval | secret manager/env |
| Rate limit cache | local memory | local memory | shared Redis-equivalent recommended |
| Monitoring | local compose | rule validation | secured Prometheus/Grafana/alerts |

## External service/data flows

| Flow | Source | Destination | Data sent | Control |
|---|---|---|---|---|
| Story generation | LangGraph | OpenAI-compatible provider | Current story state, selected choice, scoped RAG context | Timeout, retries, rate limit, no credentials in payload |
| Embedding | Retrieval ingest/query | Ollama | Lore/query text | Local service in current design |
| Vector retrieval | Retrieval service | ChromaDB | Embeddings and metadata filters | Adventure/location scoping |
| Metrics scrape | Prometheus | Django `/metrics` | Aggregated counters/histograms | Avoid PII labels |
| Browser JSON | Browser | Django views | Choices/actions/template/save commands | CSRF, session auth, body limits |

## Proof-of-concept success criteria

| Criterion | Status | Evidence |
|---|---|---|
| A user can complete a web-based adventure loop | Pass | Django pages and tests |
| AI-generated narrative can be combined with deterministic rules | Pass | LangGraph + combat integration |
| RAG limits lore to selected adventure/location | Pass | Retrieval tests and docs |
| Provider outage does not corrupt saved state | Pass | Regression tests |
| Authenticated saves are isolated by owner | Pass | Save/template authorization tests |
| Combat is safe for concurrent session states | Pass after Priority 1 | `CombatSession` and isolation test |
| Production settings can be validated by environment | Pass after Priority 1 | `check --deploy` with non-debug env |
| CI/CD and staged deployment are industrialized | Planned | Priority 4 |
| Alerting and incident runbooks are complete | Planned | Priority 5 |
