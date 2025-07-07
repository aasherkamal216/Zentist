import asyncio
import pytz
import json
import base64
import os
from dotenv import load_dotenv
from datetime import datetime, time, timedelta
from typing import List, Dict, Optional, Any

from sqlmodel import Session, select

from google.oauth2 import service_account
from googleapiclient.discovery import build

from dateutil.parser import parse as date_parse
from urllib.parse import quote_plus

from agents import function_tool, RunContextWrapper

from core.config import clinic_config as config
from dental_agents.context import AssistantContext

_: bool = load_dotenv()

# --- Google Service Caching ---
_service_cache = {}

# *** THE CORRECTED FUNCTION ***
def get_google_service(doctor_identifier: str, scopes: List[str]) -> Any:
    """Securely creates and caches a Google API service client for a specific doctor.
    It reads the doctor's credentials from an environment variable defined in clinics.json.

    Args:
        doctor_identifier (str): The email or name of the doctor.
        scopes (List[str]): The Google API scopes required.
    """
    # Sort the scopes to ensure the key is consistent regardless of order
    # Use a consistent cache key
    scopes_tuple = tuple(sorted(scopes))
    cache_key = (doctor_identifier, scopes_tuple)

    if cache_key in _service_cache:
        return _service_cache[cache_key]
    
    doctor_info = None
    for doctor in config['doctors']:
        if doctor['email'] == doctor_identifier or doctor['name'] == doctor_identifier:
            doctor_info = doctor
            break
    
    if not doctor_info:
        raise ValueError(f"Could not find configuration for doctor: {doctor_identifier}")
    
    # Get the name of the environment variable from the config
    env_var_name = doctor_info.get("google_credentials_env_var") + "_B64"
    if not env_var_name:
        raise ValueError(f"Missing 'google_credentials_env_var' setting for doctor: {doctor_identifier}")
    
    # Read the Base64 content from the environment variable
    creds_b64_str = os.getenv(env_var_name)
    if not creds_b64_str:
        raise ValueError(f"Environment variable '{env_var_name}' is not set or empty.")

    try:
        creds_json_str = base64.b64decode(creds_b64_str).decode('utf-8')
        
        creds_info = json.loads(creds_json_str)
        creds = service_account.Credentials.from_service_account_info(creds_info, scopes=scopes)
        service = build('calendar', 'v3', credentials=creds)

        _service_cache[cache_key] = service
        return service
    except json.JSONDecodeError:
        raise ValueError(f"Could not parse JSON from environment variable '{env_var_name}'.")
    except Exception as e:
        raise RuntimeError(f"Failed to create Google service for {doctor_identifier}: {e}")


def _create_google_calendar_universal_link(
    text: str,
    start_time: datetime,
    end_time: datetime,
    details: str,
    location: str,
    timezone: str
) -> str:
    """
    Creates a universal 'Add to Google Calendar' link.
    """
    # Google Calendar expects times in UTC, formatted as YYYYMMDDTHHMMSSZ
    # We must convert our timezone-aware datetimes to UTC first.
    start_utc = start_time.astimezone(pytz.utc)
    end_utc = end_time.astimezone(pytz.utc)
    
    # Format for the URL
    tfmt = "%Y%m%dT%H%M%SZ"
    
    # URL encode all parameters
    params = {
        "action": "TEMPLATE",
        "text": quote_plus(text),
        "dates": f"{start_utc.strftime(tfmt)}/{end_utc.strftime(tfmt)}",
        "details": quote_plus(details),
        "location": quote_plus(location),
        "ctz": quote_plus(timezone)
    }
    
    return f"https://www.google.com/calendar/render?{'&'.join([f'{k}={v}' for k, v in params.items()])}"


# --- AGENT TOOLS ---
@function_tool
async def find_free_slots(
    calendar_ids: List[str],
    doctor_email: str,
    time_min: str,
    time_max: str
) -> Dict[str, Any]:
    """
    Checks Google Calendar for busy times within a specified window for a list of calendars.

    Args:
        calendar_ids (List[str]): List of Google Calendar IDs to check.
        doctor_email (str): The email of the dentist whose calendar is to be checked.
        time_min (str): The start of the search window in ISO 8601 format.
        time_max (str): The end of the search window in ISO 8601 format.

    Returns:
        A dictionary containing the raw 'busy' intervals returned by the Google Free/Busy API.
    """
    try:
        service = get_google_service(doctor_email, config['general_config']['google_api_scopes_calendar'])
        body = {
            "timeMin": time_min,
            "timeMax": time_max,
            "timeZone": "America/New_York",
            "items": [{"id": cal_id} for cal_id in calendar_ids]
        }
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, lambda: service.freebusy().query(body=body).execute())
        
        # Return the raw busy data. The agent's intelligence will process this.
        return {"status": "success", "data": results['calendars']}
    except Exception as e:
        return {"status": "error", "message": f"Failed to check calendar availability: {str(e)}"}

@function_tool
async def create_appointment(
    patient_name: str,
    patient_email: str,
    doctor_email: str,
    start_datetime_iso: str,
    event_duration_minutes: int,
    service_type: str
) -> Dict[str, Any]:
    """
    Creates an appointment in Google Calendar and syncs it to the internal database (Supabase).

    Args:
        patient_name (str): Full name of the patient.
        patient_email (str): Email address of the patient for the invite.
        doctor_email (str): The email of the doctor to book an appointment with.
        start_datetime_iso (str): The start time in ISO 8601 format).
        event_duration_minutes (int): Duration of the event in minutes.
        service_type (str): The type of service (e.g., 'Teeth Whitening').

    Returns:
        A dictionary with the outcome and details of the created appointment.
    """
    try:
        
        doctor = next((doc for doc in config['doctors'] if doc["email"] == doctor_email), None)

        if doctor is None:
            raise ValueError(f"Incorrect doctor email provided.")

        tz_str = config['timezone']
        tz = pytz.timezone(tz_str)
        start_dt = date_parse(start_datetime_iso).astimezone(tz)
        end_dt = start_dt + timedelta(minutes=event_duration_minutes)

        event_summary = f"Appointment: {patient_name} - {service_type}"
        event_description = f"Patient: {patient_name}\nEmail: {patient_email}\nService: {service_type}"

        event_body = {
            'summary': event_summary,
            'location': config['clinic_address'],
            'description': event_description,
            'start': {'dateTime': start_dt.isoformat(), 'timeZone': tz_str},
            'end': {'dateTime': end_dt.isoformat(), 'timeZone': tz_str},
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # One day
                    {'method': 'popup', 'minutes': 60},
                ],
            },
        }

        service = get_google_service(doctor_email, config['general_config']['google_api_scopes_calendar'])
        loop = asyncio.get_event_loop()
        created_event = await loop.run_in_executor(None, 
            lambda: service.events().insert(
                calendarId=doctor['calendar_id'], 
                body=event_body,
                sendUpdates="all" # Send invites to attendees
            ).execute()
        )

        patient_calendar_link = _create_google_calendar_universal_link(
            text=event_summary,
            start_time=start_dt,
            end_time=end_dt,
            details=event_description,
            location=config['clinic_address'],
            timezone=tz_str
        )
        return {
            "status": "success",
            "message": "Appointment created successfully.",
            "appointment_details": {
                "patient_name": patient_name,
                "patient_email": patient_email,
                "doctor_name": doctor['name'],
                "doctor_email": doctor['email'],
                "clinic_address": config['clinic_address'],
                "start_time": start_dt.isoformat(),
                "end_time": end_dt.isoformat(),
                "service_type": service_type,
                "google_calendar_event_id": created_event.get('id'),
                "google_calendar_event_link": created_event.get('htmlLink'),
                "patient_add_to_calendar_link": patient_calendar_link
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to create appointment: {str(e)}"}

