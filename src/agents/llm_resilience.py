import os
import random
import time
from dataclasses import dataclass
from typing import Any, Callable

from django.conf import settings

from observability.metrics import (
    LLM_ATTEMPTS,
    LLM_REQUEST_DURATION,
    LLM_REQUESTS,
    LLM_RETRIES,
    LLM_STRUCTURED_OUTPUTS,
)
from pydantic import BaseModel, ValidationError


class TemporaryLLMServiceError(Exception):
    """Raised when an LLM call remains unavailable after configured retries."""


@dataclass(frozen=True)
class LLMRetryConfig:
    max_attempts: int
    initial_delay_seconds: float
    backoff_multiplier: float
    max_delay_seconds: float
    jitter_seconds: float
    transient_error_keywords: tuple[str, ...]
    transient_status_codes: tuple[int, ...]


def get_llm_setting(name: str, default: Any) -> Any:
    if settings.configured and hasattr(settings, name):
        return getattr(settings, name)
    return os.getenv(name, default)


def _as_int(value: Any) -> int:
    return int(value)


def _as_float(value: Any) -> float:
    return float(value)


def _as_keyword_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        values = value.split(",")
    else:
        values = value
    return tuple(str(keyword).strip().lower() for keyword in values if str(keyword).strip())


def _as_status_code_tuple(value: Any) -> tuple[int, ...]:
    if isinstance(value, str):
        values = value.split(",")
    else:
        values = value
    return tuple(int(status_code) for status_code in values if str(status_code).strip())


def get_llm_retry_config() -> LLMRetryConfig:
    return LLMRetryConfig(
        max_attempts=max(1, _as_int(get_llm_setting("LLM_RETRY_MAX_ATTEMPTS", "3"))),
        initial_delay_seconds=max(
            0,
            _as_float(get_llm_setting("LLM_RETRY_INITIAL_DELAY_SECONDS", "0.5")),
        ),
        backoff_multiplier=max(
            1,
            _as_float(get_llm_setting("LLM_RETRY_BACKOFF_MULTIPLIER", "2")),
        ),
        max_delay_seconds=max(
            0,
            _as_float(get_llm_setting("LLM_RETRY_MAX_DELAY_SECONDS", "4")),
        ),
        jitter_seconds=max(
            0,
            _as_float(get_llm_setting("LLM_RETRY_JITTER_SECONDS", "0.25")),
        ),
        transient_error_keywords=_as_keyword_tuple(
            get_llm_setting(
                "LLM_TRANSIENT_ERROR_KEYWORDS",
                "timeout,timed out,rate limit,too many requests,temporarily unavailable,"
                "service unavailable,connection error,connection reset,connection aborted,"
                "server error,internal server error,bad gateway,gateway timeout,try again",
            )
        ),
        transient_status_codes=_as_status_code_tuple(
            get_llm_setting(
                "LLM_TRANSIENT_STATUS_CODES",
                "408,409,425,429,500,502,503,504",
            )
        ),
    )


def is_transient_llm_error(exc: Exception, config: LLMRetryConfig | None = None) -> bool:
    config = config or get_llm_retry_config()

    status_code = getattr(exc, "status_code", None)
    response = getattr(exc, "response", None)
    if status_code is None and response is not None:
        status_code = getattr(response, "status_code", None)

    if status_code in config.transient_status_codes:
        return True

    exc_name = exc.__class__.__name__.lower()
    exc_text = str(exc).lower()
    return any(
        keyword in exc_name or keyword in exc_text
        for keyword in config.transient_error_keywords
    )


def invoke_llm_with_retries(
    invoker: Callable[[Any], Any],
    payload: Any,
    *,
    call_name: str,
) -> Any:
    config = get_llm_retry_config()
    delay = config.initial_delay_seconds
    last_error: Exception | None = None
    started_at = time.perf_counter()

    try:
        for attempt in range(1, config.max_attempts + 1):
            LLM_ATTEMPTS.labels(operation=call_name).inc()
            try:
                result = invoker(payload)
            except Exception as exc:
                last_error = exc
                if isinstance(exc, ValidationError):
                    LLM_STRUCTURED_OUTPUTS.labels(operation=call_name, status="invalid").inc()
                if not is_transient_llm_error(exc, config):
                    LLM_REQUESTS.labels(operation=call_name, status="error").inc()
                    raise
                if attempt >= config.max_attempts:
                    break

                LLM_RETRIES.labels(operation=call_name).inc()
                jitter = (
                    random.uniform(0, config.jitter_seconds)
                    if config.jitter_seconds
                    else 0
                )
                time.sleep(delay + jitter)
                delay = min(
                    config.max_delay_seconds,
                    delay * config.backoff_multiplier,
                )
            else:
                if isinstance(result, BaseModel):
                    LLM_STRUCTURED_OUTPUTS.labels(operation=call_name, status="valid").inc()
                LLM_REQUESTS.labels(operation=call_name, status="success").inc()
                return result

        LLM_REQUESTS.labels(operation=call_name, status="unavailable").inc()
        raise TemporaryLLMServiceError(
            f"{call_name} failed after {config.max_attempts} configured attempt(s)."
        ) from last_error
    finally:
        LLM_REQUEST_DURATION.labels(operation=call_name).observe(
            time.perf_counter() - started_at
        )
