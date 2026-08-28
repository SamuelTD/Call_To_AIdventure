import requests
from django.core.management.base import BaseCommand, CommandError

from agents.runtime_config import AIRuntimeConfig, AIConfigurationError


class Command(BaseCommand):
    help = "Validate AI configuration and optionally test provider connectivity."

    def add_arguments(self, parser):
        parser.add_argument("--connect", action="store_true", help="Perform safe network checks")
        parser.add_argument("--require-generation-key", action="store_true")

    def handle(self, *args, **options):
        try:
            config = AIRuntimeConfig.from_env(
                require_generation_key=options["require_generation_key"]
            )
        except AIConfigurationError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS("AI configuration is valid"))
        for key, value in config.safe_metadata().items():
            self.stdout.write(f"{key}: {value}")
        self.stdout.write(f"generation_credentials: {'present' if config.openai_api_key else 'absent'}")

        if not options["connect"]:
            return
        try:
            response = requests.get(
                f"{config.ollama_host}/api/tags",
                timeout=config.embedding_timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise CommandError("Ollama connectivity check failed") from exc
        models = {item.get("name") for item in response.json().get("models", [])}
        if config.embedding_model not in models:
            raise CommandError(f"Embedding model is unavailable: {config.embedding_model}")
        self.stdout.write(self.style.SUCCESS("Ollama and embedding model are reachable"))
