from .context import AssistantContext
from prompts.prompt_builder import build_prompts
from tools.calendar_tools import (
    find_free_slots,
    create_appointment
)
from tools.email_tools import send_booking_confirmation
from core.config import get_settings

from agents import Agent, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel

settings = get_settings()

set_tracing_disabled(True)

agents_prompts = build_prompts()

scheduler_agent = Agent[AssistantContext](
    name="Scheduler Agent",
    instructions=agents_prompts["scheduler"],
    tools=[
        create_appointment,
        find_free_slots,
        send_booking_confirmation,
    ],
    model=LitellmModel(model=settings.DEFAULT_MODEL, api_key=settings.GROQ_API_KEY),
    handoff_description="This agent specializes in appointment booking related tasks.",
)
