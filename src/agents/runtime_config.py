"""Validated, non-secret runtime configuration for AI integrations."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse


class AIConfigurationError(ValueError):
    """Raised when AI runtime configuration is internally inconsistent."""


def _positive_float(name: str, default: str) -> float:
    raw = os.getenv(name, default)
    try:
        value = float(raw)
    except ValueError as exc:
        raise AIConfigurationError(f"{name} must be a number") from exc
    if value <= 0:
        raise AIConfigurationError(f"{name} must be greater than zero")
    return value


def _non_negative_int(name: str, default: str) -> int:
    raw = os.getenv(name, default)
    try:
        value = int(raw)
    except ValueError as exc:
        raise AIConfigurationError(f"{name} must be an integer") from exc
    if value < 0:
        raise AIConfigurationError(f"{name} must be zero or greater")
    return value


def _http_url(name: str, default: str) -> str:
    value = os.getenv(name, default).rstrip("/")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise AIConfigurationError(f"{name} must be an http(s) URL")
    return value


def _bool_env(name: str, default: str) -> bool:
    value = os.getenv(name, default).strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise AIConfigurationError(f"{name} must be a boolean")


@dataclass(frozen=True)
class AIRuntimeConfig:
    openai_api_key: str | None
    openai_model: str
    reasoning_effort: str
    rag_enabled: bool
    ollama_host: str
    embedding_model: str
    request_timeout_seconds: float
    provider_max_retries: int
    embedding_timeout_seconds: float
    embedding_max_attempts: int
    max_input_chars: int
    user_turn_limit_per_hour: int

    @classmethod
    def from_env(cls, *, require_generation_key: bool = False) -> "AIRuntimeConfig":
        key = os.getenv("OPENAI_API_KEY") or None
        if require_generation_key and not key:
            raise AIConfigurationError("OPENAI_API_KEY is required for generation")
        model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna").strip()
        embedding_model = os.getenv("EMBED_MODEL", "mxbai-embed-large:latest").strip()
        if not model:
            raise AIConfigurationError("OPENAI_MODEL must not be empty")
        if not embedding_model:
            raise AIConfigurationError("EMBED_MODEL must not be empty")
        return cls(
            openai_api_key=key,
            openai_model=model,
            reasoning_effort=os.getenv("OPENAI_REASONING_EFFORT", "low").strip() or "low",
            rag_enabled=_bool_env("RAG_ENABLED", "true"),
            ollama_host=_http_url("OLLAMA_HOST", "http://localhost:11434"),
            embedding_model=embedding_model,
            request_timeout_seconds=_positive_float("LLM_REQUEST_TIMEOUT_SECONDS", "30"),
            provider_max_retries=_non_negative_int("LLM_PROVIDER_MAX_RETRIES", "0"),
            embedding_timeout_seconds=_positive_float("EMBED_REQUEST_TIMEOUT_SECONDS", "10"),
            embedding_max_attempts=max(1, _non_negative_int("EMBED_MAX_ATTEMPTS", "3")),
            max_input_chars=max(1, _non_negative_int("AI_MAX_INPUT_CHARS", "1000")),
            user_turn_limit_per_hour=_non_negative_int("AI_TURNS_PER_USER_PER_HOUR", "20"),
        )

    def safe_metadata(self) -> dict[str, object]:
        return {
            "generation_model": self.openai_model,
            "reasoning_effort": self.reasoning_effort,
            "rag_enabled": self.rag_enabled,
            "embedding_model": self.embedding_model,
            "request_timeout_seconds": self.request_timeout_seconds,
            "provider_max_retries": self.provider_max_retries,
            "embedding_timeout_seconds": self.embedding_timeout_seconds,
            "embedding_max_attempts": self.embedding_max_attempts,
            "max_input_chars": self.max_input_chars,
            "turns_per_user_per_hour": self.user_turn_limit_per_hour,
        }
