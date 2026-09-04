import json
import sqlite3
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from data_pipeline.normalize import normalize, parse_challenge_rating
from data_pipeline.pipeline import run_pipeline
from data_pipeline.schemas import RawMonster, SourceName, utc_now
from data_pipeline.sources import load_json_source


def monster(name="Goblin", **overrides):
    record = {
        "name": name,
        "armor": "15",
        "HP": "12",
        "challenge_rating": "1/4",
        "strength": "+1",
        "dexterity": "+2",
        "constitution": "+0",
        "intelligence": "-1",
        "wisdom": "+0",
        "charisma": "-1",
        "description": " test ",
    }
    record.update(overrides)
    return record


def write_json(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


class DataPipelineTests(unittest.TestCase):
    def test_scraper_json_lines_metadata_is_loaded(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "scraped.jsonl"
            record = {
                **monster(),
                "source_record_id": "external-42",
                "source_url": "https://example.test/monster/42",
                "collected_at": "2026-08-28T09:00:00Z",
            }
            path.write_text(json.dumps(record) + "\n", encoding="utf-8")
            loaded = load_json_source(path, SourceName.SCRAPED)
            self.assertEqual(loaded[0].source_record_id, "external-42")
            self.assertEqual(loaded[0].source_url, "https://example.test/monster/42")
            self.assertNotIn("collected_at", loaded[0].payload)

    def test_fractional_challenge_rating_is_preserved(self):
        value, raw = parse_challenge_rating("1/4")
        self.assertEqual(str(value), "0.25")
        self.assertEqual(raw, "1/4")

    def test_normalization_parses_fields_and_stable_key(self):
        raw = RawMonster(
            source=SourceName.CURATED,
            source_record_id="Élite Goblin",
            collected_at=utc_now(),
            payload=monster(
                "Élite Goblin", gold_loot=[2, 8], items_loot=[" coin ", ""]
            ),
        )
        result = normalize(raw)
        self.assertEqual(result.stable_key, "elite-goblin")
        self.assertEqual(result.hp, 12)
        self.assertEqual(result.description, "test")
        self.assertEqual(result.items_loot, ["coin"])

    def test_pipeline_merges_and_persists_provenance(self):
        with TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            curated = tmp_path / "curated.json"
            scraped = tmp_path / "scraped.json"
            database = tmp_path / "monsters.db"
            write_json(curated, [monster(HP="20"), monster("Broken", HP="invalid")])
            write_json(scraped, [monster(HP="10"), monster("Wolf", HP="8")])
            result = run_pipeline(
                curated_path=curated,
                scraped_path=scraped,
                output_dir=tmp_path / "runs",
                db_path=database,
            )
            self.assertEqual(result.manifest.collected, 4)
            self.assertEqual(result.manifest.accepted_source_records, 3)
            self.assertEqual(result.manifest.rejected, 1)
            self.assertEqual(result.manifest.merged, 2)
            self.assertEqual(result.manifest.conflicts, 1)
            goblin = next(
                item for item in result.monsters if item.monster.name == "Goblin"
            )
            self.assertEqual(goblin.monster.hp, 20)
            self.assertEqual(len(goblin.sources), 2)

            connection = sqlite3.connect(database)
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM monsters").fetchone()[0], 2
            )
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM monster_sources").fetchone()[0],
                3,
            )
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM rejected_records").fetchone()[0],
                1,
            )
            connection.close()

    def test_pipeline_output_is_json_lines(self):
        with TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            curated = tmp_path / "curated.json"
            scraped = tmp_path / "scraped.json"
            write_json(curated, [monster()])
            write_json(scraped, [])
            result = run_pipeline(
                curated_path=curated,
                scraped_path=scraped,
                output_dir=tmp_path / "runs",
            )
            clean_path = Path(result.manifest.output_files["cleaned"])
            self.assertEqual(
                len(clean_path.read_text(encoding="utf-8").splitlines()), 1
            )
            self.assertEqual(
                json.loads(clean_path.read_text(encoding="utf-8"))["monster"]["name"],
                "Goblin",
            )


if __name__ == "__main__":
    unittest.main()
