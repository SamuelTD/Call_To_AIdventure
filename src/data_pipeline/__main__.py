from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import run_pipeline
from utils.pathing import PROJECT_ROOT


DEFAULT_CURATED_PATH = PROJECT_ROOT / "data/documents/monsters.json"
DEFAULT_SCRAPED_PATH = PROJECT_ROOT / "monster_scrapping/monsters.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data/pipeline/runs"
DEFAULT_DB_PATH = PROJECT_ROOT / "db/sqlite/data.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize, merge, and store the certification monster dataset."
    )
    parser.add_argument("--curated", type=Path, default=DEFAULT_CURATED_PATH)
    parser.add_argument("--scraped", type=Path, default=DEFAULT_SCRAPED_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--no-database", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_pipeline(
        curated_path=args.curated,
        scraped_path=args.scraped,
        output_dir=args.output_dir,
        db_path=None if args.no_database else args.db_path,
    )
    manifest = result.manifest
    print(
        f"Pipeline {manifest.run_id}: collected={manifest.collected}, "
        f"accepted={manifest.accepted_source_records}, rejected={manifest.rejected}, "
        f"merged={manifest.merged}, conflicts={manifest.conflicts}"
    )
    print(f"Manifest: {manifest.output_files['manifest']}")


if __name__ == "__main__":
    main()
