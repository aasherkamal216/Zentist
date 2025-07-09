import chainlit as cl
from supabase import create_client, Client
from gotrue.errors import AuthApiError
import httpx
import json
from typing import Optional

from core.config import get_settings

import os
from dotenv import load_dotenv

_ = load_dotenv()

settings = get_settings()
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# --- STAGE 1: AUTHENTICATION ---
@cl.password_auth_callback
def auth_callback(email: str, password: str) -> Optional[cl.User]:

    try:
        # Attempt to sign in the user to get a session object.
        print(f"Attempting to sign in user: {email}")
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        
        print(f"User {email} signed in successfully.")
        # Pass the token in the metadata for the next step.
        return cl.User(identifier=res.user.email, metadata={"token": res.session.access_token})

    except AuthApiError as e:
        if "Invalid login credentials" in str(e):
            print(f"Sign-in failed for {email}, attempting to sign up.")
            try:
                # If login fails, try to sign them up.
                res = supabase.auth.sign_up({"email": email, "password": password})
                print(f"User {email} signed up successfully.")
                
                # Immediately sign in after signup to get a valid session.
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                print(f"User {email} signed in after signup.")
                return cl.User(identifier=res.user.email, metadata={"token": res.session.access_token})
            
            except AuthApiError as signup_error:
                print(f"Supabase Auth Error during sign-up for {email}: {signup_error}")
                return None # Signup failed (e.g., password too weak)
        else:
            print(f"Unhandled Supabase Auth Error for {email}: {e}")
            return None # Other auth error

    except Exception as e:
        print(f"An unexpected error occurred during authentication for {email}: {e}")
        return None

# --- STAGE 2: SESSION INITIALIZATION ---
@cl.on_chat_start
async def start_chat():
    """
    This function runs AFTER successful authentication and has the correct context.
    This is the proper place to set session variables.
    """
    # Retrieve the user object created by the auth_callback
    current_user = cl.user_session.get("user")
    
    # Retrieve the token from the metadata and store it in the session
    token = current_user.metadata.get("token")
    cl.user_session.set("supabase_token", token)
    
    # Initialize other session state
    cl.user_session.set("conversation_id", None)


# --- CHAT LOGIC (Handles communication with FastAPI backend) ---
@cl.on_message
async def handle_message(message: cl.Message):
    supabase_token = cl.user_session.get("supabase_token")
    conversation_id = cl.user_session.get("conversation_id")

    if not supabase_token:
        await cl.Message(content="Authentication token not found. Your session may have expired. Please refresh and log in again.").send()
        return

    headers = {
        "Authorization": f"Bearer {supabase_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "user_message": message.content,
        "conversation_id": conversation_id
    }

    # Prepare UI elements for streaming
    final_msg = cl.Message(content="")
    agent_step_removed = {"status": False} 
    tool_steps = {}

    try:
        async with cl.Step(name="Thinking...", type="llm", show_input=False) as agent_step:
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", f"{os.getenv('BACKEND_URL')}/api/v1/chat/stream", headers=headers, json=payload, timeout=300) as response:
                    response.raise_for_status()
                    
                    async for chunk in response.aiter_text():
                        for line in chunk.splitlines():
                            if line.startswith('data:'):
                                json_data = line[5:].strip()
                                if not json_data: continue
                                try:
                                    stream_event = json.loads(json_data)
                                    await handle_stream_event(stream_event, agent_step, final_msg, tool_steps, agent_step_removed)
                                except json.JSONDecodeError:
                                    print(f"Warning: Could not decode JSON from stream: '{json_data}'")
    
    except Exception as e:
        await cl.Message(content=f"Sorry, an error occurred: {e}").send()


async def handle_stream_event(event_data, agent_step, final_msg, tool_steps, agent_step_removed):
    event_type = event_data.get("event")
    data = event_data.get("data", {})

    if event_type == "conversation_id":
        cl.user_session.set("conversation_id", data.get("id"))
    
    elif event_type == "text":
        if not agent_step_removed["status"]:
            await agent_step.remove()
            agent_step_removed["status"] = True

        for token in data.get("delta", ""):
            await final_msg.stream_token(token)
            
    elif event_type == "end":
        await final_msg.send()