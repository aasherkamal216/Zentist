from agents import Agent, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel

from .context import AssistantContext

from prompts import build_prompts
from core.config import get_settings

settings = get_settings()

set_tracing_disabled(True)

agents_prompts = build_prompts()

receptionist_agent = Agent[AssistantContext](
    name="Receptionist Agent",
    instructions=agents_prompts["receptionist"],
    model=LitellmModel(model=settings.DEFAULT_MODEL, api_key=settings.GROQ_API_KEY),
    handoff_description="This agent specializes in general questions-answering about our clinic."
)