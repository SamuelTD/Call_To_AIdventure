import os

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

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
OPENAI_REASONING_EFFORT = os.getenv("OPENAI_REASONING_EFFORT", "low")

llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model=OPENAI_MODEL,
    reasoning_effort=OPENAI_REASONING_EFFORT,
    use_responses_api=True,
    timeout=float(get_llm_setting("LLM_REQUEST_TIMEOUT_SECONDS", "30")),
    max_retries=int(get_llm_setting("LLM_PROVIDER_MAX_RETRIES", "0")),
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
