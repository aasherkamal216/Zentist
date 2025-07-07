from agents import handoff
from agents.extensions import handoff_filters

from .receptionist import receptionist_agent
from .canceling import canceling_agent
from .scheduler import scheduler_agent 
from .context import AssistantContext

# Link receptionist handoffs
receptionist_agent.handoffs = [
    handoff(
        agent=scheduler_agent, input_filter=handoff_filters.remove_all_tools
    ),
    handoff(
        agent=canceling_agent, input_filter=handoff_filters.remove_all_tools
    )
]

# Link canceling handoffs
canceling_agent.handoffs = [
    handoff(agent=receptionist_agent, input_filter=handoff_filters.remove_all_tools)
]

# Optional but good practice: define what gets exported from this package
__all__ = [
    "receptionist_agent",
    "canceling_agent",
    "scheduler_agent",
    "AssistantContext",
]