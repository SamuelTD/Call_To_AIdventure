import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from data_pipeline.pipeline import run_pipeline


def monster(name, hp, challenge="1/4"):
    return {
        "name": name,
        "armor": "12",
        "HP": str(hp),
        "challenge_rating": challenge,
        "strength": "+0",
        "dexterity": "+1",
        "constitution": "+0",
        "intelligence": "-1",
        "wisdom": "+0",
        "charisma": "-1",
        "description": "Fixture monster",
    }


class DatasetApiTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.directory = TemporaryDirectory()
        root = Path(cls.directory.name)
        curated = root / "curated.json"
        scraped = root / "scraped.json"
        curated.write_text(
            json.dumps([monster("Goblin", 12), monster("Dragon", 100, "4")]),
            encoding="utf-8",
        )
        scraped.write_text(json.dumps([monster("Goblin", 10)]), encoding="utf-8")
        cls.database = root / "dataset.db"
        cls.result = run_pipeline(
            curated_path=curated,
            scraped_path=scraped,
            output_dir=root / "runs",
            db_path=cls.database,
        )
        cls.settings_override = override_settings(DATASET_DB_PATH=str(cls.database))
        cls.settings_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.settings_override.disable()
        cls.directory.cleanup()
        super().tearDownClass()

    def test_collection_supports_pagination_filtering_and_ordering(self):
        response = self.client.get(
            "/api/v1/monsters/",
            {"challenge_min": "1", "ordering": "-hp", "page_size": "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["name"], "Dragon")

    def test_collection_rejects_invalid_query(self):
        response = self.client.get("/api/v1/monsters/", {"page_size": "101"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "invalid_query")

    def test_openapi_and_interactive_documentation_are_available(self):
        specification = self.client.get("/api/v1/openapi.yaml")
        self.assertEqual(specification.status_code, 200)
        self.assertEqual(specification["Content-Type"], "application/yaml")
        documentation = self.client.get("/api/v1/docs/")
        self.assertContains(documentation, "SwaggerUIBundle")

    def test_detail_includes_provenance(self):
        collection = self.client.get("/api/v1/monsters/", {"search": "Goblin"}).json()
        monster_id = collection["results"][0]["id"]
        response = self.client.get(f"/api/v1/monsters/{monster_id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["sources"]), 2)

    def test_run_summary_requires_staff(self):
        run_id = self.result.manifest.run_id
        self.assertEqual(
            self.client.get(f"/api/v1/ingestion-runs/{run_id}/summary/").status_code,
            401,
        )
        user = User.objects.create_user("normal", password="test-password")
        self.client.force_login(user)
        self.assertEqual(
            self.client.get(f"/api/v1/ingestion-runs/{run_id}/summary/").status_code,
            403,
        )
        user.is_staff = True
        user.save()
        self.assertEqual(
            self.client.get(f"/api/v1/ingestion-runs/{run_id}/summary/").status_code,
            200,
        )
