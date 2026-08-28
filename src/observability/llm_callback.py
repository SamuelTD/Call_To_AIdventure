"""Privacy-preserving LangChain callback for provider-reported usage."""

from __future__ import annotations

import os

from langchain_core.callbacks import BaseCallbackHandler

from observability.metrics import LLM_ESTIMATED_COST_USD, LLM_TOKEN_USAGE


class AIUsageMetricsCallback(BaseCallbackHandler):
    def on_llm_end(self, response, **kwargs):
        output = response.llm_output or {}
        usage = output.get("token_usage") or output.get("usage") or {}
        model = str(output.get("model_name") or os.getenv("OPENAI_MODEL", "unknown"))
        input_tokens = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
        output_tokens = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
        if input_tokens:
            LLM_TOKEN_USAGE.labels(direction="input", model=model).inc(input_tokens)
        if output_tokens:
            LLM_TOKEN_USAGE.labels(direction="output", model=model).inc(output_tokens)

        input_rate = float(os.getenv("AI_INPUT_COST_USD_PER_MILLION_TOKENS", "0"))
        output_rate = float(os.getenv("AI_OUTPUT_COST_USD_PER_MILLION_TOKENS", "0"))
        estimated = (input_tokens * input_rate + output_tokens * output_rate) / 1_000_000
        if estimated:
            LLM_ESTIMATED_COST_USD.labels(model=model).inc(estimated)
