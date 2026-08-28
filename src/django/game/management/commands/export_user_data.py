import json
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from game.models import CharacterTemplate, SaveGame


class Command(BaseCommand):
    help = "Export the personal data associated with one Django user."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("--output", type=Path)

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username=options["username"])
        except User.DoesNotExist as exc:
            raise CommandError("User does not exist") from exc
        payload = {
            "account": {
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "date_joined": user.date_joined.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
            },
            "save_games": list(
                SaveGame.objects.filter(user=user).values(
                    "id", "adventure_id", "adventure_name", "state", "is_finished",
                    "finished_at", "created_at", "updated_at",
                )
            ),
            "character_templates": list(
                CharacterTemplate.objects.filter(user=user).values(
                    "id", "name", "race", "character_class", "gender",
                    "created_at", "updated_at",
                )
            ),
        }
        content = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
        output = options.get("output")
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(content, encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Export written to {output}"))
        else:
            self.stdout.write(content)
