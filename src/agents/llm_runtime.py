from dotenv import load_dotenv

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

AI_CONFIG = AIRuntimeConfig.from_env()
OPENAI_API_KEY = AI_CONFIG.openai_api_key
OPENAI_MODEL = AI_CONFIG.openai_model
OPENAI_REASONING_EFFORT = AI_CONFIG.reasoning_effort

llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model=OPENAI_MODEL,
    reasoning_effort=OPENAI_REASONING_EFFORT,
    use_responses_api=True,
    timeout=float(get_llm_setting("LLM_REQUEST_TIMEOUT_SECONDS", "30")),
    max_retries=int(get_llm_setting("LLM_PROVIDER_MAX_RETRIES", "0")),
    callbacks=[AIUsageMetricsCallback()],
)

base_story_template = ChatPromptTemplate.from_template("{full_prompt}")
story_chain = base_story_template | llm | StrOutputParser()

summary_chain = SUMMARY_TEMPLATE | llm | StrOutputParser()
summary_chain_fr = SUMMARY_TEMPLATE_FR | llm | StrOutputParser()

choicer_model = llm.with_structured_output(ChoiceOutput)
choicer_chain = CHOOSER_TEMPLATE | choicer_model
choicer_chain_fr = CHOOSER_TEMPLATE_FR | choicer_model

goal_evaluator_model = llm.with_structured_output(GoalEvaluationOutput)
goal_evaluator_chain = base_story_template | goal_evaluator_model

room_completion_model = llm.with_structured_output(RoomCompletionOutput)
room_completion_chain = base_story_template | room_completion_model


def build_thinker_agent():
    return create_agent(llm, tools)
