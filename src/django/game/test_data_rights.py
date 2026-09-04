from datetime import timedelta
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from game.models import CharacterTemplate, SaveGame


class DataRightsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("subject", email="subject@example.test")
        self.save = SaveGame.objects.create(
            user=self.user,
            adventure_id="fixture",
            adventure_name="Fixture",
            state={"story": "personal game state"},
            is_finished=True,
            finished_at=timezone.now() - timedelta(days=400),
        )
        CharacterTemplate.objects.create(
            user=self.user,
            name="Hero",
            race="Human",
            character_class="Warrior",
            gender="Other",
        )

    def test_user_deletion_cascades_to_owned_data(self):
        user_id = self.user.id
        self.user.delete()
        self.assertFalse(SaveGame.objects.filter(user_id=user_id).exists())
        self.assertFalse(CharacterTemplate.objects.filter(user_id=user_id).exists())

    def test_export_contains_account_saves_and_templates(self):
        output = StringIO()
        call_command("export_user_data", "subject", stdout=output)
        content = output.getvalue()
        self.assertIn("subject@example.test", content)
        self.assertIn("personal game state", content)
        self.assertIn("Hero", content)

    def test_retention_is_dry_run_unless_apply_is_passed(self):
        call_command("cleanup_retention", days=365, stdout=StringIO())
        self.assertTrue(SaveGame.objects.filter(pk=self.save.pk).exists())
        call_command("cleanup_retention", days=365, apply=True, stdout=StringIO())
        self.assertFalse(SaveGame.objects.filter(pk=self.save.pk).exists())
