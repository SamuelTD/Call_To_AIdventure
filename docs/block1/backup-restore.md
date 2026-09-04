# Backup and restoration procedure

## Public game dataset

The monster database is derived data. Its authoritative inputs are the
versioned source snapshots, adventures and pipeline code. Restore it with:

```bash
uv run python db/sqlite/setup_db.py --reset
```

Verify the restored counts and indexes with:

```bash
uv run python db/sqlite/explain_queries.py --db-path db/sqlite/data.db
```

## Django personal-data database

Create an application-level backup in an access-controlled directory ignored
by Git:

```bash
mkdir -p data/exports
uv run python src/django/manage.py dumpdata \
  --natural-foreign --natural-primary --indent 2 \
  -o data/exports/django-backup.json
```

Restore only into a clean, access-controlled environment after migrations:

```bash
uv run python src/django/manage.py migrate
uv run python src/django/manage.py loaddata data/exports/django-backup.json
```

The backup contains account and gameplay data and may include password hashes.
Encrypt it at rest, restrict operator access, define a deletion date, and never
commit or use it as public certification evidence. Test restoration with a
non-production or anonymized backup before relying on the procedure.
