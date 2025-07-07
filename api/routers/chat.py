import json
import uuid
from typing import Dict, Optional
from dateutil.parser import parse as date_parse

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlmodel import Session

from agents import (
    Agent,
    Runner,
    RunResultStreaming,
    ToolCallItem,
    ToolCallOutputItem,
)

from openai.types.responses import ResponseTextDeltaEvent

from dental_agents import receptionist_agent, scheduler_agent, canceling_agent, AssistantContext
from api.db.cache import get_redis_client
from api.db.session import get_db_session
from api.security.auth import get_current_user, User
from api.models.appointment import Appointment
from tools.calendar_tools import create_appointment as create_appointment_tool

router = APIRouter()

# --- Pydantic Models for API Contract ---
class ChatRequest(BaseModel):
    user_message: str
    conversation_id: Optional[str] = None

class StreamEvent(BaseModel):
    event: str
    data: dict

# --- Agent Registry & State ---
AGENTS_REGISTRY: Dict[str, Agent] = {
    receptionist_agent.name: receptionist_agent,
    scheduler_agent.name: scheduler_agent,
    canceling_agent.name: canceling_agent
}
DEFAULT_AGENT_NAME = receptionist_agent.name
SESSION_TTL_SECONDS = 3600  # 1 hour

@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis_client),
    db: Session = Depends(get_db_session)
):
    """
    Handles a chat message, manages session state in Redis, and streams back the agent's response.
    """
    conversation_id = request.conversation_id or f"session_{uuid.uuid4().hex}"
    redis_key = f"user_session:{user.id}:{conversation_id}"

    # 1. Retrieve current state from Redis
    stored_state = await redis.get(redis_key)
    if stored_state:
        state = json.loads(stored_state)
        message_history = state.get("chat_history", [])
        last_agent_name = state.get("last_agent_name", DEFAULT_AGENT_NAME)
    else:
        message_history, last_agent_name = [], DEFAULT_AGENT_NAME

    active_agent = AGENTS_REGISTRY.get(last_agent_name, AGENTS_REGISTRY[DEFAULT_AGENT_NAME])
    dental_context = AssistantContext(db=db, user=user)

    async def stream_generator():
        # Yield the conversation ID first if it's a new conversation
        if not request.conversation_id:
            initial_event = StreamEvent(event="conversation_id", data={"id": conversation_id})
            yield f"data: {initial_event.model_dump_json()}\n\n"

        current_input = message_history + [{"role": "user", "content": request.user_message}]
        
        result: RunResultStreaming = Runner.run_streamed(
            active_agent, current_input, context=dental_context
        )

        # Create a temporary map to store tool call names
        tool_call_name_map: Dict[str, str] = {}

        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                stream_event = StreamEvent(event="text", data={"delta": event.data.delta})
                yield f"data: {stream_event.model_dump_json()}\n\n"

            elif event.type == "agent_updated_stream_event":
                stream_event = StreamEvent(event="handoff", data={"new_agent": event.new_agent.name})
                yield f"data: {stream_event.model_dump_json()}\n\n"
            elif event.type == "run_item_stream_event":
                item = event.item
                if isinstance(item, ToolCallItem):
                    tool_call_name_map[item.raw_item.call_id] = item.raw_item.name

                    stream_event = StreamEvent(event="tool_start", data=item.raw_item.model_dump())
                    yield f"data: {stream_event.model_dump_json()}\n\n"

                elif isinstance(item, ToolCallOutputItem):
                    output_data = {"call_id": item.raw_item.get("call_id"), "output": str(item.output)}
                    stream_event = StreamEvent(event="tool_end", data=output_data)
                    yield f"data: {stream_event.model_dump_json()}\n\n"

                    call_id = item.raw_item.get("call_id")
                    tool_name = tool_call_name_map.get(call_id)

                    if tool_name == create_appointment_tool.name:
                        tool_output = item.output
                        if isinstance(tool_output, dict) and tool_output.get("status") == "success":
                            details = tool_output.get("appointment_details", {})
                            try:
                                # Ensure datetime objects are correctly parsed
                                start_time = date_parse(details.get("start_time"))
                                end_time = date_parse(details.get("end_time"))

                                new_appointment = Appointment(
                                    patient_name=details.get("patient_name"),
                                    patient_email=details.get("patient_email"),
                                    patient_supabase_id=user.id,
                                    doctor_name=details.get("doctor_name"),
                                    doctor_email=details.get("doctor_email"),
                                    clinic_address=details.get("clinic_address"),
                                    service_type=details.get("service_type"),
                                    start_time=start_time,
                                    end_time=end_time,
                                    google_calendar_event_id=details.get("google_calendar_event_id"),
                                    google_calendar_event_link=details.get("google_calendar_event_link")
                                )

                                db.add(new_appointment)
                                db.commit()
                                db.refresh(new_appointment)
                            except Exception as e:
                                print(f"❌ DATABASE ERROR: Failed to save appointment. Error: {e}")
                                db.rollback()

        # After the stream is complete, save the final state to Redis.
        new_history = result.to_input_list()
        new_agent_name = result.last_agent.name
        new_state = {"chat_history": new_history, "last_agent_name": new_agent_name}
        await redis.set(redis_key, json.dumps(new_state), ex=SESSION_TTL_SECONDS)

        # Signal the end of the stream
        end_event = StreamEvent(event="end", data={})
        yield f"data: {end_event.model_dump_json()}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")
