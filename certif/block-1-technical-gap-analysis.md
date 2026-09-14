# Block 1 — Technical Coverage and Gap Analysis

## Purpose

This document assesses the current technical coverage of certification Block 1:
**Collect, store, and make available the data of an artificial intelligence
project**.

It covers competencies C1 to C5. It is a technical gap analysis, not yet the
final professional report. Its purpose is to identify:

1. what the current application already demonstrates;
2. what is currently missing;
3. what can become demonstrable with a limited amount of focused work;
4. what technical evidence should be retained for the certification report and
   oral examination.

The analysis only counts the active Django application and reusable data tools.
Legacy files are excluded. The optional monster scraping workspace is counted
as an existing prototype, but not as an integrated production pipeline.

## Executive assessment

The application already has a real data flow:

```text
Adventure JSON files ---------+
                              +--> validation/transformation --> SQLite --> Django services
Monster JSON file ------------+

World lore JSON --> chunking --> embeddings --> ChromaDB --> RAG retrieval --> LLM prompts
```

It also contains a separate Scrapy prototype capable of collecting monster
data from a website. These elements provide a useful starting point for Block
1, but they do not yet form one documented, tested, multi-source data pipeline.

The shortest credible route to coverage is to turn the monster data flow into
a standalone certification pipeline:

```text
Scraped monster data ----+
                         +--> staging --> validation --> normalization --> SQLite
Curated monster JSON ----+
                                                         |
                                                         +--> documented REST API
```

This gives the block one coherent subject: collecting monster data from two
sources, cleaning and merging it, storing it in a modeled database, then
making it available through an authenticated and documented REST API.

### Status summary

| Competency | Current status | Realistic status after focused work |
|---|---|---|
| C1 — Automated data extraction | Partially covered | Coverable |
| C2 — SQL extraction queries | Partially covered | Coverable |
| C3 — Multi-source aggregation | Not covered | Coverable |
| C4 — Database creation and GDPR | Partially covered | Coverable |
| C5 — REST data API | Partially covered | Coverable |

No big-data platform is currently used. A big-data component should not be
added merely for appearance unless the training organization confirms that it
is mandatory for the selected evaluation scenario. It would add substantial
complexity without improving the application. The report must state this
scope decision explicitly.

## Existing technical assets

The following current components can be retained and improved:

- `monster_scrapping/monster_scraping/`: Scrapy extraction prototype for
  monster statistics;
- `data/documents/monsters.json`: curated monster source file;
- `data/world/adventures/*/*.json`: structured adventure sources;
- `data/world/characters/*.json` and `data/world/locations/*.json`: structured
  world-lore sources;
- `db/sqlite/setup_db.py`: repeatable creation and population of the game-data
  SQLite database;
- `src/utils/adventure.py`: parameterized SQL reads for adventures;
- `src/utils/monster.py`: parameterized SQL lookup for monsters;
- `src/retrieval/ingest.py` and `src/retrieval/chunker.py`: validation,
  transformation and ingestion of lore data;
- `src/django/game/views.py`: JSON endpoints used by the browser application;
- Django models and migrations for user-owned saves and character templates;
- Git history and installation documentation.

These assets prove that data is genuinely used by the final application. They
must, however, be connected by a reproducible process and supported by
technical evidence.

---

## C1 — Automate data extraction

### What is covered by the application

- The project reads structured data from several files programmatically:
  monster JSON, adventure JSON, character JSON and location JSON.
- `db/sqlite/setup_db.py` provides a command-line entry point and imports
  monster and adventure data into SQLite.
- The Scrapy prototype extracts monster attributes from web pages.
- The active application performs parameterized extraction from SQLite.
- The RAG ingestion code reads, validates and transforms structured lore files.
- The extraction and import source code is versioned in Git.

### What is not covered

- The scraper is not connected to the active import pipeline.
- Scraped output is not stored in a clearly defined staging format.
- The scraper assumes that expected HTML elements exist and has insufficient
  handling for missing or malformed fields.
- There is no unified command that runs extraction, validation, normalization
  and persistence from start to finish.
- There is no execution report containing source, date, record counts,
  rejected records and errors.
- Source constraints are not documented: terms of use, robots policy,
  request rate, data license, confidentiality and expected HTML structure.
- There is no REST source or big-data source in the current collection
  pipeline.
- The repository does not contain extraction specifications defining the
  expected fields and acceptance rules.

### What can become covered with limited work

Build a small, robust extraction command around the monster dataset:

1. Correct the Scrapy field selectors and parsing defects.
2. Define a raw/staging monster schema with source metadata:
   `source`, `source_url`, `collected_at`, and `source_record_id`.
3. Export scraper results to a deterministic JSON Lines file in a staging
   directory.
4. Add timeouts, retry rules, rate limiting, missing-field handling and clear
   error messages.
5. Make the scraper configurable so that a small fixture or local HTML sample
   can be used during tests without contacting the live website.
6. Add a single CLI entry point for collection, for example:
   `python -m data_pipeline collect --source scraped-monsters`.
7. Produce a machine-readable run manifest with counts for collected,
   accepted, rejected and failed records.
8. Add automated tests using saved HTML fixtures.

Reading the existing curated JSON file and scraping the website would provide
the required multi-source basis without changing the game itself.

### Evidence to retain

- extraction specification;
- source and legal-constraint analysis;
- command and dependency documentation;
- sample raw output and run manifest;
- scraper tests and test results;
- screenshots or terminal output of a successful run;
- Git commit containing the implementation.

---

## C2 — Develop SQL extraction queries

### What is covered by the application

- SQLite is an actual runtime dependency rather than a demonstration-only
  database.
- Adventures are loaded through parameterized `SELECT` statements.
- Monsters are retrieved case-insensitively through a parameterized query.
- The import script uses explicit SQL schemas and parameterized inserts.
- Django ORM queries enforce ownership when loading or deleting user data.

### What is not covered

- There is no SQL query catalogue.
- Selection, filtering and ordering choices are not explained in relation to a
  business or collection objective.
- There are no joins or aggregate extraction queries demonstrating a prepared
  dataset.
- Index choices and query plans are not documented.
- No performance comparison or `EXPLAIN QUERY PLAN` output is retained.
- SQL behavior has little direct automated test coverage.
- There is no big-data query language or system.

### What can become covered with limited work

1. Create a documented SQL query file used to produce the final monster
   dataset required by the application.
2. Include meaningful filters, for example valid HP, supported challenge
   rating and enabled source records.
3. Add provenance tables so a query can join normalized monsters to their
   source records and ingestion runs.
4. Add indexes that correspond to real access patterns, such as normalized
   monster name and source record lookup.
5. Record `EXPLAIN QUERY PLAN` before and after indexing.
6. Test that the queries return the expected rows and reject or exclude invalid
   records.
7. Document each query's purpose, parameters, filters, joins and optimization
   choices.

The queries should remain part of the application or pipeline rather than
being artificial examples created only for the report.

### Evidence to retain

- versioned SQL query file;
- query catalogue and purpose of every query;
- test database fixture and expected results;
- query-plan evidence;
- schema and index definitions;
- automated test output.

---

## C3 — Aggregate data from different sources

### What is covered by the application

- The current import code performs a few transformations, including numeric
  parsing, loot serialization and default values.
- Pydantic models validate several runtime and RAG data structures.
- The RAG chunker converts heterogeneous character and location documents into
  a common chunk representation.

These are useful building blocks, but they do not yet demonstrate the C3
requirement for a cleaned and normalized dataset aggregated from different
sources.

### What is not covered

- There is no explicit aggregation of scraped monsters and curated monsters.
- There is no canonical field mapping per source.
- There is no deterministic duplicate-resolution rule.
- Corrupted, incomplete and non-normalized records are not collected in a
  rejection dataset.
- Data quality rules and acceptable thresholds are not specified.
- There is no final raw/clean dataset distinction.
- The aggregation process has no run summary or lineage information.
- The current challenge-rating parser loses fractional values, which is a data
  quality problem for values such as `1/2` or `1/4`.

### What can become covered with limited work

Implement a focused ETL step for monsters:

1. Define one canonical Pydantic schema for a monster record.
2. Map every input source to that schema.
3. Normalize names, numeric armor and HP values, challenge ratings, ability
   modifiers, loot and empty values.
4. Preserve fractional challenge ratings using an appropriate numeric or text
   representation.
5. Define mandatory fields and validation ranges.
6. Send rejected records to a separate file with a reason code.
7. Merge records using a documented stable key.
8. Define precedence rules when sources disagree.
9. Keep provenance for every merged record.
10. Produce cleaned JSON or CSV plus a data-quality report before database
    import.
11. Add unit tests for missing fields, malformed numbers, duplicates,
    conflicting sources and fractional ratings.

This is the largest missing technical element of Block 1, but it is contained:
it can be implemented without changing the narrative, combat or LLM layers.

### Evidence to retain

- source-to-canonical mapping table;
- raw sample from each source;
- clean and rejected output samples;
- documented normalization and deduplication rules;
- data-quality metrics before and after cleaning;
- automated aggregation tests;
- pipeline run manifest.

---

## C4 — Create a database and address GDPR requirements

### What is covered by the application

- `db/sqlite/setup_db.py` creates the game-data schema and imports records.
- The application uses a separate Django database for accounts, saves and
  character templates.
- Django migrations make the application schema reproducible.
- Foreign keys and ownership relations exist for user-created data.
- Installation instructions explain how to build both databases.
- User-owned saves and character templates can be deleted through the
  application.

### What is not covered

- There is no conceptual data model or Merise MCD/MLD.
- The choice of SQLite is not justified against the scope, volume, concurrency
  and deployment constraints.
- The game-data schema has weak constraints and stores several lists as JSON
  text.
- There is no explicit staging, provenance or ingestion-run schema.
- There is no GDPR processing register.
- Personal-data purposes, legal basis, recipients and retention periods are
  not documented.
- There is no automated retention or account-deletion procedure.
- There is no documented export, rectification or erasure procedure.
- There is no test proving that deleting a user cascades to their saves and
  templates.
- Database backup, restoration and production security are not addressed.

### What can become covered with limited work

1. Produce a Merise MCD and MLD covering users, saves, character templates,
   monsters, source records and ingestion runs.
2. Document why SQLite is suitable for the local certification demonstration
   and state when PostgreSQL would be required.
3. Add constraints and indexes that support the final model.
4. Store ingestion provenance and run information.
5. Write a GDPR processing register for account and save-game data.
6. Define retention periods, for example for inactive accounts, finished games
   and technical logs.
7. Implement a management command for retention cleanup with a `--dry-run`
   option.
8. Document and test user-data deletion and export.
9. Ensure secrets and generated databases are excluded from Git.
10. Document backup and restore commands for the demonstration environment.

The monster and adventure datasets are not personal data, but user accounts,
character templates and saved games may be. The report must clearly separate
these two categories.

### Evidence to retain

- MCD and MLD diagrams;
- physical schema and migrations;
- database-choice decision record;
- GDPR processing register;
- retention and deletion procedure;
- cleanup command and tests;
- backup/restore demonstration;
- successful clean-install and import output.

---

## C5 — Make the dataset available through a REST API

### What is covered by the application

- Django exposes JSON over HTTP to the browser.
- The adventure-list endpoint makes stored adventure data available.
- Other endpoints expose character options, templates, saves and active game
  state.
- User-owned saves and templates are filtered by the authenticated user.
- Inputs receive some validation and errors use HTTP status codes.
- Endpoint behavior is exercised by the Django test suite.

### What is not covered

- There is no clearly identified dataset API for normalized monster data.
- There is no OpenAPI specification or interactive API documentation.
- Dataset endpoints do not use a consistent authentication and authorization
  policy.
- Many write endpoints are exempted from CSRF protection.
- There is no API version prefix.
- There is no pagination, filtering contract or standardized error schema.
- There is no rate limiting.
- Request and response schemas are not centrally declared.
- The existing architecture document is not a complete endpoint reference.
- There are no API security tests covering every access rule.

### What can become covered with limited work

Create a small versioned REST API focused on the Block 1 dataset:

```text
GET /api/v1/monsters/
GET /api/v1/monsters/{id}/
GET /api/v1/ingestion-runs/{id}/summary/
```

Recommended work:

1. Define response and error schemas.
2. Add filtering and pagination to the monster collection.
3. Add an authentication mechanism appropriate to the demonstration, or
   explicitly define public read access and authenticated administrative
   access.
4. Restore normal CSRF protection for session-authenticated write operations.
5. Generate an OpenAPI document covering every certification endpoint.
6. Add endpoint tests for success, validation, authentication, authorization,
   absence of data and pagination.
7. Document example requests and responses.
8. Add a minimal rate-limit or document the reverse-proxy control expected in
   production.

The API does not need to expose every internal game endpoint. A small,
well-specified API around the cleaned monster dataset is easier to defend and
directly demonstrates C5.

### Evidence to retain

- OpenAPI file and rendered documentation;
- endpoint inventory;
- authentication and authorization rules;
- example requests and responses;
- automated API test results;
- security decisions and production recommendations;
- live demonstration retrieving the cleaned dataset.

---

## Recommended implementation plan

### Priority 1 — Create the certification data pipeline

- choose the scraped and curated monster sources;
- define raw and canonical schemas;
- make scraping reproducible from fixtures;
- normalize, validate, deduplicate and retain rejected records;
- generate a data-quality run manifest.

This work primarily closes C1 and C3.

### Priority 2 — Improve storage and SQL evidence

- add source and ingestion-run tables;
- create the MCD, MLD and physical schema;
- add useful extraction queries and indexes;
- test queries and record query plans.

This work primarily closes C2 and the technical portion of C4.

### Priority 3 — Add the dataset API

- expose the cleaned monsters through `/api/v1/`;
- add schemas, filtering, pagination and access rules;
- publish OpenAPI documentation;
- add API and security tests.

This work primarily closes C5.

### Priority 4 — Complete GDPR and operational procedures

- create the processing register;
- define retention, export and deletion procedures;
- implement and test cleanup/export commands;
- document backup and restoration.

This closes the compliance portion of C4.

## Definition of done for Block 1

Block 1 should be considered technically ready for report writing when all of
the following statements are true:

- one command can collect or load data from at least two defined sources;
- raw source data is retained separately from cleaned output;
- invalid data is rejected with explicit reason codes;
- aggregation and normalization rules are deterministic and tested;
- every final record retains source provenance;
- the final dataset is imported into a documented database schema;
- SQL extraction queries are functional, documented and tested;
- an MCD, MLD and physical model exist;
- GDPR processing and retention procedures cover all personal data;
- the cleaned dataset is available through a versioned, tested REST API;
- the API has explicit access rules and OpenAPI documentation;
- installation and execution can be reproduced from a clean checkout;
- successful test and pipeline outputs are retained as evidence in the report.

## Scope warning

The existing code should not be described as fully compliant before the above
work is completed. In particular:

- the Scrapy prototype is evidence of an attempted extraction, not yet a
  reliable data-collection pipeline;
- loading two independent JSON categories into a database is not, by itself,
  multi-source aggregation;
- existing browser JSON endpoints are not, by themselves, a documented and
  secured dataset API;
- functional SQLite databases do not replace the required data models and GDPR
  procedures.

The positive point is that the missing work is localized. It can be added as a
data-engineering layer around the existing monster dataset without rewriting
the game application.
