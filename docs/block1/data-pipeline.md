# Block 1 monster data pipeline

## Objective and sources

The pipeline combines two explicitly identified inputs:

| Source | Role | Location | Precedence |
|---|---|---|---|
| Scraped monster snapshot | Externally collected statistics | `monster_scrapping/monsters.json` | Lower |
| Curated game dataset | Internal corrections, descriptions and loot | `data/documents/monsters.json` | Higher |

Both current snapshots contain 510 named records. They differ on five game
records. The curated source wins deterministic conflicts; every source link is
still stored in `monster_sources`. These inputs are related rather than wholly
independent. Certification acceptance of them as separate sources must be
confirmed with the evaluator.

## Execution

From the repository root:

```bash
PYTHONPATH=src uv run python -m data_pipeline
```

The normal database build invokes the same pipeline:

```bash
uv run python db/sqlite/setup_db.py --reset
```

Each run creates a timestamped directory under `data/pipeline/runs` containing
raw JSON Lines, cleaned JSON Lines, rejected JSON Lines, and a JSON manifest.
Generated runs are ignored by Git because source payloads may be large. Retain
one sanitized run as report evidence outside the application repository.

## Acceptance and normalization rules

- `name`, `armor`, and `HP` are mandatory.
- Names are trimmed and converted to an accent-insensitive stable key.
- Armor and HP extract their integer component; HP must be positive.
- Ability modifiers are integers from -20 to 20.
- Challenge rating accepts integers, decimals and fractions. `None`, `N/A`,
  empty and unknown values become SQL `NULL`; original text is retained.
- Loot defaults to an empty list and a zero-to-zero gold range.
- A malformed record is retained in `rejected.jsonl` with reason code
  `VALIDATION_ERROR`; it is not silently discarded.
- Matching uses the normalized stable name key.
- Curated values win conflicts, while provenance records identify all inputs
  and the selected source.

The manifest records collected, accepted, rejected, merged and conflicting
record counts. The committed snapshots currently produce 1,020 accepted source
records, 510 merged monsters, and five conflicts.

## Scraping constraints

The extraction code obeys robots rules, uses an identifying user agent, limits
concurrency, delays requests, retries transient errors and has a timeout. The
site currently presents automated clients with a verification page, so the
offline fixture is the reproducible certification evidence. A live extraction
must only be run after manually confirming current terms, robots policy and
licensing.
