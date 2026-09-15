import random
import string
from sqlmodel import Session, select
from app.db.models import Incident, User, FollowUp, Institution, Student
from app.models.schemas import TriageResult
from datetime import datetime
from typing import Optional


# ── Incidents ─────────────────────────────────────────────

def save_incident(
    session: Session,
    student_name: str,
    report_text: str,
    result: TriageResult,
    reported_by: str,
    student_code: str = "",
) -> Incident:
    incident = Incident(
        student_name=student_name,
        student_code=student_code or None,
        report_text=report_text,
        category=result.category.value,
        urgency_level=result.urgency_level.value,
        department=result.department.value,
        summary=result.summary,
        reasoning=result.reasoning,
        provider=result.provider,
        model_name=result.model,
        latency_ms=result.latency_ms,
        tokens_used=result.tokens_used,
        estimated_cost_usd=result.estimated_cost_usd,
        reported_by=reported_by,
    )
    session.add(incident)
    session.commit()
    session.refresh(incident)
    return incident


def get_student_history(session: Session, student_code: str) -> list[Incident]:
    if not student_code:
        return []
    stmt = (
        select(Incident)
        .where(Incident.student_code == student_code)
        .order_by(Incident.created_at.desc())
    )
    return list(session.exec(stmt).all())


def get_student_by_code(session: Session, code: str) -> Optional[Student]:
    return session.exec(select(Student).where(Student.code == code.upper())).first()


def confirm_incident(session: Session, incident_id: int) -> Optional[Incident]:
    incident = session.get(Incident, incident_id)
    if incident:
        incident.confirmed = True
        session.commit()
        session.refresh(incident)
    return incident


def redirect_incident(
    session: Session,
    incident_id: int,
    department: Optional[str] = None,
    urgency_level: Optional[str] = None,
    redirect_reason: str = "",
    redirected_by: str = "",
) -> Optional[Incident]:
    incident = session.get(Incident, incident_id)
    if not incident:
        return None
    if department:
        incident.department = department
    if urgency_level:
        incident.urgency_level = urgency_level
    incident.redirect_reason = redirect_reason
    incident.redirected_by   = redirected_by
    session.add(incident)
    session.commit()
    session.refresh(incident)
    return incident


def get_all_incidents(session: Session, department: str | None = None) -> list[Incident]:
    stmt = select(Incident)
    if department:
        stmt = stmt.where(Incident.department == department)
    stmt = stmt.order_by(Incident.created_at.desc())
    return list(session.exec(stmt).all())


# ── Users ─────────────────────────────────────────────────

def get_user_by_username(session: Session, username: str) -> Optional[User]:
    return session.exec(select(User).where(User.username == username)).first()


def get_all_users(session: Session) -> list[User]:
    return list(session.exec(select(User)).all())


# ── Follow-ups ────────────────────────────────────────────

def save_followup(
    session: Session,
    incident_id: int,
    department: str,
    scheduled_date: datetime,
    notes: str,
    created_by: str,
) -> FollowUp:
    fu = FollowUp(
        incident_id=incident_id,
        department=department,
        scheduled_date=scheduled_date,
        notes=notes,
        created_by=created_by,
    )
    session.add(fu)
    session.commit()
    session.refresh(fu)
    return fu


def get_followups_by_department(session: Session, department: str | None = None) -> list[FollowUp]:
    stmt = select(FollowUp)
    if department:
        stmt = stmt.where(FollowUp.department == department)
    stmt = stmt.order_by(FollowUp.scheduled_date.asc())
    return list(session.exec(stmt).all())


# ── Institutions ──────────────────────────────────────────

def _generate_code() -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=8))


def create_institution(session: Session, name: str) -> Institution:
    for _ in range(10):
        code = _generate_code()
        existing = session.exec(select(Institution).where(Institution.code == code)).first()
        if not existing:
            break
    institution = Institution(name=name, code=code)
    session.add(institution)
    session.commit()
    session.refresh(institution)
    return institution


def get_institution_by_code(session: Session, code: str) -> Optional[Institution]:
    return session.exec(select(Institution).where(Institution.code == code)).first()


def get_all_institutions(session: Session) -> list[Institution]:
    return list(session.exec(select(Institution)).all())


# ── Additional User functions ─────────────────────────────

def get_user_by_email(session: Session, email: str) -> Optional[User]:
    return session.exec(select(User).where(User.email == email)).first()


def create_user(
    session: Session,
    email: str,
    first_name: str,
    last_name: str,
    role: str,
    department: Optional[str],
    institution_code: Optional[str],
    hashed_password: str,
) -> User:
    name = f"{first_name} {last_name}".strip()
    user = User(
        username=email,
        hashed_password=hashed_password,
        name=name,
        role=role,
        department=department,
        email=email,
        first_name=first_name,
        last_name=last_name,
        institution_code=institution_code,
        temp_password=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def change_user_password(session: Session, user_id: int, hashed_password: str) -> Optional[User]:
    user = session.get(User, user_id)
    if not user:
        return None
    user.hashed_password = hashed_password
    user.temp_password = False
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def delete_user(session: Session, user_id: int) -> bool:
    user = session.get(User, user_id)
    if not user:
        return False
    session.delete(user)
    session.commit()
    return True


def get_user_by_id(session: Session, user_id: int) -> Optional[User]:
    return session.get(User, user_id)


def delete_institution(session: Session, institution_id: int) -> bool:
    inst = session.get(Institution, institution_id)
    if not inst:
        return False
    session.delete(inst)
    session.commit()
    return True


# ── Save incident from TriageResult directly ──────────────

def save_incident_from_result(
    session: Session,
    student_name: str,
    report_text: str,
    result: TriageResult,
    reported_by: str,
    student_code: str = "",
) -> Incident:
    incident = Incident(
        student_name=student_name,
        student_code=student_code or None,
        report_text=report_text,
        category=result.category.value,
        urgency_level=result.urgency_level.value,
        department=result.department.value,
        summary=result.summary,
        reasoning=result.reasoning,
        provider=result.provider,
        model_name=result.model,
        latency_ms=result.latency_ms,
        tokens_used=result.tokens_used,
        estimated_cost_usd=result.estimated_cost_usd,
        reported_by=reported_by,
    )
    session.add(incident)
    session.commit()
    session.refresh(incident)
    return incident
