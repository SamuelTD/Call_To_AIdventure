from dotenv import load_dotenv
from functools import lru_cache

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import create_agent

from agents.schemas import ChoiceOutput, GoalEvaluationOutput, RoomCompletionOutput
from agents.tools import tools
from agents.prompts import (
    CHOOSER_TEMPLATE,
    SUMMARY_TEMPLATE,
)
from agents.prompts.chooser import CHOOSER_TEMPLATE_FR
from agents.prompts.summary import SUMMARY_TEMPLATE_FR
from agents.llm_resilience import get_llm_setting
from agents.runtime_config import AIRuntimeConfig
from observability.llm_callback import AIUsageMetricsCallback

load_dotenv()

base_story_template = ChatPromptTemplate.from_template("{full_prompt}")


class LazyRuntimeObject:
    def __init__(self, factory):
        self._factory = factory

    @property
    def _target(self):
        return self._factory()

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return getattr(self._target, name)

    def invoke(self, *args, **kwargs):
        return self._target.invoke(*args, **kwargs)


@lru_cache(maxsize=1)
def get_llm():
    config = AIRuntimeConfig.from_env(require_generation_key=True)
    return ChatOpenAI(
        api_key=config.openai_api_key,
        model=config.openai_model,
        reasoning_effort=config.reasoning_effort,
        use_responses_api=True,
        timeout=float(get_llm_setting("LLM_REQUEST_TIMEOUT_SECONDS", "30")),
        max_retries=int(get_llm_setting("LLM_PROVIDER_MAX_RETRIES", "0")),
        callbacks=[AIUsageMetricsCallback()],
    )


llm = LazyRuntimeObject(get_llm)

story_chain = LazyRuntimeObject(
    lambda: base_story_template | get_llm() | StrOutputParser()
)
summary_chain = LazyRuntimeObject(lambda: SUMMARY_TEMPLATE | get_llm() | StrOutputParser())
summary_chain_fr = LazyRuntimeObject(
    lambda: SUMMARY_TEMPLATE_FR | get_llm() | StrOutputParser()
)
choicer_chain = LazyRuntimeObject(
    lambda: CHOOSER_TEMPLATE | get_llm().with_structured_output(ChoiceOutput)
)
choicer_chain_fr = LazyRuntimeObject(
    lambda: CHOOSER_TEMPLATE_FR | get_llm().with_structured_output(ChoiceOutput)
)
goal_evaluator_chain = LazyRuntimeObject(
    lambda: base_story_template
    | get_llm().with_structured_output(GoalEvaluationOutput)
)
room_completion_chain = LazyRuntimeObject(
    lambda: base_story_template
    | get_llm().with_structured_output(RoomCompletionOutput)
)


def build_thinker_agent():
    return create_agent(get_llm(), tools)
