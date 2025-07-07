from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from datetime import date
from sqlmodel import Session, select

from api.db.session import get_db_session
from api.security.auth import get_current_user, User
from api.models.appointment import Appointment

router = APIRouter()

@router.get("/", response_model=List[Appointment])
def get_doctor_appointments(
    start_date: Optional[date] = Query(None, description="Filter by start date (e.g., 2024-08-01)"),
    end_date: Optional[date] = Query(None, description="Filter by end date (e.g., 2024-08-31)"),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves appointments for the currently authenticated doctor.
    The doctor is identified by the email in their JWT.
    """
    statement = select(Appointment).where(Appointment.doctor_email == current_user.email)
    
    if start_date:
        statement = statement.where(Appointment.start_time >= start_date)
    if end_date:
        statement = statement.where(Appointment.start_time <= end_date)
        
    statement = statement.order_by(Appointment.start_time.asc())
    
    appointments = db.exec(statement).all()
    return appointments