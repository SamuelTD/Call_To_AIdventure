import argparse
import sqlite3


QUERIES = {
    "name lookup": "SELECT * FROM monsters WHERE name = ? COLLATE NOCASE",
    "challenge filter": "SELECT id, name FROM monsters WHERE challenge_rating BETWEEN ? AND ?",
    "source lookup": "SELECT monster_id FROM monster_sources WHERE source = ? AND source_record_id = ?",
}


def main():
    parser = argparse.ArgumentParser(description="Print SQLite query-plan evidence.")
    parser.add_argument("--db-path", default="db/sqlite/data.db")
    args = parser.parse_args()
    connection = sqlite3.connect(args.db_path)
    parameters = {
        "name lookup": ("Goblin Warrior",),
        "challenge filter": (0, 5),
        "source lookup": ("curated_monsters", "Goblin Warrior"),
    }
    try:
        for name, query in QUERIES.items():
            print(f"[{name}]")
            for row in connection.execute(
                f"EXPLAIN QUERY PLAN {query}", parameters[name]
            ):
                print(" | ".join(str(value) for value in row))
    finally:
        connection.close()


if __name__ == "__main__":
    main()
