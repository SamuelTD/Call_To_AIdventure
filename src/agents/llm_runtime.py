import os
import random

from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import create_agent

from agents.schemas import ChoiceOutput, GoalEvaluationOutput
from agents.tools import tools
from agents.prompts import (
    CHOOSER_TEMPLATE,
    SUMMARY_TEMPLATE,
)

load_dotenv()

seed = random.randrange(2**32)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=GROQ_MODEL,
    temperature=0.5,
    model_kwargs={"seed": seed},
)

base_story_template = ChatPromptTemplate.from_template("{full_prompt}")
story_chain = base_story_template | llm | StrOutputParser()

summary_chain = SUMMARY_TEMPLATE | llm | StrOutputParser()

choicer_model = llm.with_structured_output(ChoiceOutput)
choicer_chain = CHOOSER_TEMPLATE | choicer_model

goal_evaluator_model = llm.with_structured_output(GoalEvaluationOutput)
goal_evaluator_chain = base_story_template | goal_evaluator_model


def build_thinker_agent():
    return create_agent(llm, tools)
