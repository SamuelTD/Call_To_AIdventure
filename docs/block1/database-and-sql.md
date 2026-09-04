# Database model and SQL catalogue

## Database decision

SQLite is appropriate for this local certification demonstration: the dataset
has hundreds rather than millions of rows, the pipeline has one writer, and the
game/API workload is read-heavy. PostgreSQL should replace it for multiple
concurrent writers, replicated deployment, stronger operational controls or
substantially larger datasets.

Personal/application data remains in Django's database. Public monster and
adventure data remains in the pipeline-managed game database. This separation
reduces unnecessary mixing of personal and public reference data.

## Logical model

```text
INGESTION_RUN 1 ─── * MONSTER
      │                 │
      │                 └── 1 ─── * MONSTER_SOURCE
      └── 1 ─── * REJECTED_RECORD

DJANGO_USER 1 ─── * SAVE_GAME
      └─────────── * CHARACTER_TEMPLATE
```

`MONSTER_SOURCE` is the association and lineage entity connecting each
canonical monster to its source records. `selected` states which source won the
merge. The physical schema, constraints and indexes are defined in
`src/data_pipeline/storage.py`.

## Query catalogue

The executable catalogue is `db/sqlite/queries/monster_dataset.sql`:

1. `Q1` prepares the valid, ordered application dataset.
2. `Q2` joins monsters to source lineage using a parameterized monster ID.
3. `Q3` aggregates ingestion quality counts and distinct source count.
4. `Q4` groups monsters by challenge rating and calculates average HP/armor.

Indexes support case-insensitive name lookup, challenge filtering, source
record lookup and lineage joins. Capture evidence after a clean build with:

```bash
uv run python db/sqlite/explain_queries.py --db-path db/sqlite/data.db
```
