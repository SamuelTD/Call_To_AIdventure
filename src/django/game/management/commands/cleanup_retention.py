from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from game.models import SaveGame


class Command(BaseCommand):
    help = "Delete finished save games older than the documented retention period."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=365)
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Perform deletion. Without this flag the command is a dry run.",
        )

    def handle(self, *args, **options):
        days = options["days"]
        if days < 1:
            raise CommandError("--days must be at least 1")
        cutoff = timezone.now() - timedelta(days=days)
        candidates = SaveGame.objects.filter(
            is_finished=True,
            finished_at__lt=cutoff,
        )
        count = candidates.count()
        if options["apply"]:
            candidates.delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted {count} finished save game(s)."))
        else:
            self.stdout.write(
                f"Dry run: {count} finished save game(s) would be deleted. "
                "Pass --apply to perform deletion."
            )
