import asyncio
from typing import Dict, Any
from dateutil.parser import parse as date_parse

# SendGrid specific imports
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To, Subject, HtmlContent

from .email_templates import PATIENT_CONFIRMATION_HTML, DOCTOR_NOTIFICATION_HTML, CANCELLATION_CONFIRMATION_HTML

from agents import function_tool

from core.config import get_settings

settings = get_settings()

# --- Helper for sending a single email ---
async def _send_email_task(
    recipient: str, 
    subject: str, 
    html_body: str, 
    client: SendGridAPIClient,
    from_email: From
) -> Dict[str, Any]:
    """Internal helper to create and send one email using SendGrid."""
    message = Mail(
        from_email=from_email,
        to_emails=To(recipient),
        subject=Subject(subject),
        html_content=HtmlContent(html_body)
    )
    try:
        loop = asyncio.get_event_loop()
        # The sendgrid library's send method is synchronous, so we run it in an executor
        response = await loop.run_in_executor(None, lambda: client.send(message))
        
        if 200 <= response.status_code < 300:
            return {"recipient": recipient, "status": "success", "status_code": response.status_code}
        else:
            return {"recipient": recipient, "status": "error", "status_code": response.status_code, "body": response.body}
            
    except Exception as e:
        print(f"ERROR sending SendGrid email to {recipient}: {e}")
        return {"recipient": recipient, "status": "error", "message": str(e)}


@function_tool
async def send_booking_confirmation(
    patient_name: str,
    patient_email: str,
    doctor_name: str,
    doctor_email: str,
    clinic_address: str,
    start_time_iso: str,
    end_time_iso: str,
    service_type: str,
    google_event_link: str,
    patient_add_to_calendar_link: str,
) -> Dict[str, Any]:
    """
    Sends professional booking confirmation emails to both the patient and the doctor.
    This single tool handles all formatting and sending logic.

    Args:
        patient_name (str): Full name of the patient.
        patient_email (str): Email address of the patient.
        doctor_name (str): Name of the assigned doctor.
        doctor_email (str): Email address of the doctor for notification.
        clinic_address (str): Full address of the clinic.
        start_time_iso (str): The appointment start time in ISO 8601 format (e.g., 2024-12-29T10:00:00-04:00).
        end_time_iso (str): The appointment end time in ISO 8601 format (e.g., 2024-12-29T10:00:00-05:00).
        service_type (str): A user-friendly description of the service.
        google_event_link (str): The direct link for the DOCTOR to view the event.
        patient_add_to_calendar_link (str): The universal link for the PATIENT to add the event.

    Returns:
        A dictionary summarizing the outcome of the email sending operations.
    """
    # --- 1. Prepare Data and Client ---
    try:
        api_key = settings.SENDGRID_API_KEY
        from_address = settings.SENDGRID_FROM_EMAIL
        from_name = settings.SENDGRID_FROM_NAME

        if not all([api_key, from_address, from_name]):
            raise ValueError("SendGrid API key, from_email, or from_name is not configured")

        sendgrid_client = SendGridAPIClient(api_key)
        from_email_obj = From(email=from_address, name=from_name)
        
        start_dt = date_parse(start_time_iso)
        end_dt = date_parse(end_time_iso)
        
        formatted_date = start_dt.strftime("%A, %B %d, %Y")
        formatted_time = start_dt.strftime("%I:%M %p %Z")
        duration_minutes = int((end_dt - start_dt).total_seconds() / 60)

    except Exception as e:
        return {"status": "error", "message": f"Failed during data preparation: {e}", "email_statuses": []}

    # --- 2. Craft Email Bodies ---
    patient_html = PATIENT_CONFIRMATION_HTML.format(
        patient_name=patient_name, service_type=service_type,
        formatted_date=formatted_date, formatted_time=formatted_time,
        duration_minutes=duration_minutes, doctor_name=doctor_name,
        clinic_address=clinic_address,
        google_event_link=google_event_link,
        patient_add_to_calendar_link=patient_add_to_calendar_link
    )
    
    doctor_html = DOCTOR_NOTIFICATION_HTML.format(
        doctor_name=doctor_name, patient_name=patient_name,
        patient_email=patient_email, service_type=service_type,
        formatted_date=formatted_date, formatted_time=formatted_time,
        google_event_link=google_event_link
    )

    # --- 3. Create and Run Sending Tasks Concurrently ---
    tasks = [
        _send_email_task(patient_email, f"Appointment Confirmation", patient_html, sendgrid_client, from_email_obj),
        _send_email_task(doctor_email, f"[New Booking] {patient_name} - {formatted_date}", doctor_html, sendgrid_client, from_email_obj)
    ]
    
    results = await asyncio.gather(*tasks)
    all_successful = all(res['status'] == 'success' for res in results)
    
    return {
        "status": "success" if all_successful else "partial_failure",
        "message": "Email confirmation process finished via SendGrid.",
        "email_statuses": results
    }

@function_tool
async def send_cancellation_email(
    patient_name: str,
    patient_email: str,
    service_type: str,
    start_time_iso: str
) -> Dict[str, Any]:
    """Sends a cancellation confirmation email to the patient.
    
    Args:
        patient_name (str): Full name of the patient.
        patient_email (str): Email address of the patient.
        start_time_iso (str): The appointment start time in ISO 8601 format (e.g., 2024-12-29T10:00:00-04:00).
        service_type (str): A user-friendly description of the service.

    Returns:
        The status of cancellation email sending process (success or error)
    """
    try:
        api_key = settings.SENDGRID_API_KEY
        from_email_obj = From(email=settings.SENDGRID_FROM_EMAIL, name=settings.SENDGRID_FROM_NAME)
        sendgrid_client = SendGridAPIClient(api_key)

        start_dt = date_parse(start_time_iso)
        
        formatted_date = start_dt.strftime("%A, %B %d, %Y")
        formatted_time = start_dt.strftime("%I:%M %p %Z")

        html_body = CANCELLATION_CONFIRMATION_HTML.format(
            patient_name=patient_name,
            service_type=service_type,
            formatted_date=formatted_date,
            formatted_time=formatted_time
        )

        email_task = _send_email_task(
            patient_email,
            f"Cancellation Confirmation",
            html_body,
            sendgrid_client,
            from_email_obj,
        )
        result = await email_task
        if result["status"] == "success":
            return {"status": "success", "message": "Cancellation email sent successfully."}
        else:
            return result
    except Exception as e:
        return {"status": "error", "message": f"Failed during email preparation: {e}"}