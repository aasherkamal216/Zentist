from typing import Optional
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel
from sqlalchemy import func, Column, DateTime

class Appointment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_name: str
    patient_email: str
    patient_supabase_id: str = Field(index=True) # The 'sub' claim from the JWT

    doctor_name: str
    doctor_email: str = Field(index=True) # index for fast lookups on the dashboard
    clinic_address: str

    service_type: str

    start_time: datetime = Field(
        sa_column=Column(DateTime(timezone=True), index=True)
    )
    end_time: datetime = Field(
        sa_column=Column(DateTime(timezone=True))
    )

    google_calendar_event_id: str
    google_calendar_event_link: str

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
        default=None,
    )