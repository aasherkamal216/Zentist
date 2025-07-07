import pytz
from datetime import datetime
from core.config import get_clinic_config

def build_prompts():
    """
    Loads clinic config and dynamically constructs a comprehensive "Operational Manual"
    that is shared across all agents, followed by their specific role instructions.
    """

    data = get_clinic_config()

    # A. Current Time Context
    primary_timezone_str = data["general_config"]["default_timezone"]
    primary_tz = pytz.timezone(primary_timezone_str)
    current_time_str = datetime.now(primary_tz).strftime("%A, %B %d, %Y at %I:%M %p %Z")
    current_time_iso = datetime.now(primary_tz).isoformat()
    
    time_context_md = f"## 1. Current System Time\n- **Current Date & Time:** `{current_time_iso}` ({current_time_str})\n- Use this as your absolute reference for all relative time queries like 'today', 'tomorrow', or 'next week'.\n"

    # B. Build structured clinic details
    clinic_details_md = f"""## 2. Clinic Details
**Name:** {data['clinic_name']}
**Address:** {data['clinic_address']}  
**Phone:** {data['clinic_phone']}
---

### 🕒 Clinic Days and Hours

| Day       | Hours                |
|-----------|----------------------|
"""

    for day, hours in data["clinic_hours"].items():
        clinic_details_md += f"| {day:<9} | {hours:<20} |\n"

    clinic_details_md += "\n\n### Doctors\n\n"

    clinic_details_md += "| Name            | Specialty                    | Email                       |\n"
    clinic_details_md += "|-----------------|------------------------------|-----------------------------|\n"
    for doc in data["doctors"]:
        clinic_details_md += f"| {doc['name']} | {doc['specialty']} | {doc['email']} |\n"

    clinic_details_md += "\n\n### Services & Durations\n\n"
    clinic_details_md += "| Service                        | Duration (minutes) |\n"
    clinic_details_md += "|--------------------------------|---------------------|\n"

    for service, duration in data["services"].items():
        clinic_details_md += f"| {service:<30} | {duration:<19} |\n"

    # C. Assemble the complete manual
    OPERATIONAL_MANUAL = f"""
# OPERATIONAL MANUAL FOR DENTAL CLINIC

This is your complete source of truth. Refer to this manual for all operational questions.

{time_context_md}
{clinic_details_md}
"""
    
    RECEPTIONIST_INSTRUCTIONS="""
"""
    SCHEDULER_INSTRUCTIONS="""
"""
    CANCELING_INSTRUCTIONS="""
"""
    return {
        'receptionist': RECEPTIONIST_INSTRUCTIONS,
        'scheduler': SCHEDULER_INSTRUCTIONS,
        'canceling': CANCELING_INSTRUCTIONS
    }
