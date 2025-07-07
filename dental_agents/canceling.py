from .context import AssistantContext
from prompts.prompt_builder import build_prompts
from tools.calendar_tools import (
    find_upcoming_appointments,
    cancel_appointment
)
from .receptionist import receptionist_agent
from tools.email_tools import send_cancellation_email
from core.config import get_settings

from agents import Agent, handoff, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel
from agents.extensions import handoff_filters

settings = get_settings()

set_tracing_disabled(True)

agents_prompts = build_prompts()

canceling_agent = Agent[AssistantContext](
    name="Canceling Agent",
    instructions=agents_prompts["canceling"],
    tools=[
        find_upcoming_appointments,
        cancel_appointment,
        send_cancellation_email,
    ],
    model=LitellmModel(model=settings.DEFAULT_MODEL, api_key=settings.GROQ_API_KEY),
    handoffs=[
        handoff(agent=receptionist_agent, input_filter=handoff_filters.remove_all_tools)
    ],
    handoff_description="This agent specializes in appointment cancellation tasks.",
)
