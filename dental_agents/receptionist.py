from agents import Agent, handoff, set_tracing_disabled
from agents.extensions import handoff_filters
from agents.extensions.models.litellm_model import LitellmModel

from .context import AssistantContext
from .scheduler import scheduler_agent
from .canceling import canceling_agent

from prompts.prompt_builder import build_prompts
from core.config import get_settings

settings = get_settings()

set_tracing_disabled(True)

agents_prompts = build_prompts()

receptionist_agent = Agent[AssistantContext](
    name="Receptionist Agent",
    instructions=agents_prompts["receptionist"],
    model=LitellmModel(model=settings.DEFAULT_MODEL, api_key=settings.GROQ_API_KEY),
    handoffs=[
        handoff(
            agent=scheduler_agent, input_filter=handoff_filters.remove_all_tools
        ),
        handoff(
            agent=canceling_agent, input_filter=handoff_filters.remove_all_tools
        )
    ],
    handoff_description="This agent specializes in general questions-answering about our clinic."
)