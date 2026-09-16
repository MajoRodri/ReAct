"""Capa de acceso a datos: todas las operaciones CRUD contra la BD SQLite."""

import random
import string
from sqlmodel import Session, select
from app.db.models import Incident, User, FollowUp, Institution, Student, ExternalContact
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
    """Persiste un incidente construido a partir de un TriageResult y devuelve el objeto con id."""
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
    """Devuelve todos los incidentes de un estudiante ordenados por fecha descendente.

    Acepta múltiples códigos separados por coma y desduplicada por id
    para cubrir el caso de un alumno con alias o cambio de código.
    """
    if not student_code:
        return []
    codes = [c.strip() for c in student_code.split(',') if c.strip()]
    seen, result = set(), []
    for code in codes:
        stmt = (
            select(Incident)
            .where(Incident.student_code.like(f"%{code}%"))
            .order_by(Incident.created_at.desc())
        )
        for inc in session.exec(stmt).all():
            if inc.id not in seen:
                seen.add(inc.id)
                result.append(inc)
    return sorted(result, key=lambda x: x.created_at, reverse=True)


def get_student_by_code(session: Session, code: str) -> Optional[Student]:
    """Busca un estudiante por su código (normalizado a mayúsculas)."""
    return session.exec(select(Student).where(Student.code == code.upper())).first()


def get_all_students(session: Session) -> list[Student]:
    """Devuelve todos los estudiantes ordenados alfabéticamente por nombre."""
    return list(session.exec(select(Student).order_by(Student.full_name)).all())


def create_student(session: Session, code: str, full_name: str, institution_code: Optional[str] = None) -> Student:
    """Registra un nuevo estudiante; el código se almacena en mayúsculas."""
    student = Student(code=code.upper(), full_name=full_name, grade="", institution_code=institution_code)
    session.add(student)
    session.commit()
    session.refresh(student)
    return student


def confirm_incident(session: Session, incident_id: int, confirmed_by: str = "") -> Optional[Incident]:
    """Marca un incidente como confirmado y guarda el nombre del profesional que lo confirmó."""
    incident = session.get(Incident, incident_id)
    if incident:
        incident.confirmed    = True
        incident.confirmed_by = confirmed_by or None
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
    """Actualiza el departamento o urgencia de un incidente; registra quién redirigió y por qué."""
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
    """Devuelve todos los incidentes; filtra por departamento si se especifica."""
    stmt = select(Incident)
    if department:
        stmt = stmt.where(Incident.department == department)
    stmt = stmt.order_by(Incident.created_at.desc())
    return list(session.exec(stmt).all())


# ── Users ─────────────────────────────────────────────────

def get_user_by_username(session: Session, username: str) -> Optional[User]:
    """Busca un usuario por su nombre de usuario (email)."""
    return session.exec(select(User).where(User.username == username)).first()


def get_all_users(session: Session) -> list[User]:
    """Devuelve todos los usuarios del sistema (usado por el panel de admin)."""
    return list(session.exec(select(User)).all())


# ── Follow-ups ────────────────────────────────────────────

def save_followup(
    session: Session,
    incident_id: int,
    department: str,
    scheduled_date: datetime,
    notes: str,
    created_by: str,
    urgency_level: str = "baja",
) -> FollowUp:
    """Crea una nueva cita de seguimiento vinculada a un incidente."""
    fu = FollowUp(
        incident_id=incident_id,
        department=department,
        scheduled_date=scheduled_date,
        notes=notes,
        created_by=created_by,
        urgency_level=urgency_level,
    )
    session.add(fu)
    session.commit()
    session.refresh(fu)
    return fu


def update_followup(
    session: Session,
    followup_id: int,
    scheduled_date: datetime,
    notes: str,
) -> Optional[FollowUp]:
    """Modifica la fecha/hora y las notas de una cita existente."""
    fu = session.get(FollowUp, followup_id)
    if not fu:
        return None
    fu.scheduled_date = scheduled_date
    fu.notes = notes
    session.add(fu)
    session.commit()
    session.refresh(fu)
    return fu


def get_followups_by_department(session: Session, department: str | None = None) -> list[FollowUp]:
    """Devuelve citas ordenadas por fecha ascendente; filtra por departamento si se indica."""
    stmt = select(FollowUp)
    if department:
        stmt = stmt.where(FollowUp.department == department)
    stmt = stmt.order_by(FollowUp.scheduled_date.asc())
    return list(session.exec(stmt).all())


# ── Institutions ──────────────────────────────────────────

def _generate_code() -> str:
    """Genera un código alfanumérico aleatorio de 8 caracteres para una institución."""
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=8))


def create_institution(session: Session, name: str) -> Institution:
    """Crea una institución con código único; reintenta hasta 10 veces ante colisiones."""
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
    """Busca una institución por su código de acceso."""
    return session.exec(select(Institution).where(Institution.code == code)).first()


def get_all_institutions(session: Session) -> list[Institution]:
    """Devuelve todas las instituciones registradas."""
    return list(session.exec(select(Institution)).all())


# ── Additional User functions ─────────────────────────────

def get_user_by_email(session: Session, email: str) -> Optional[User]:
    """Busca un usuario por su email (distinto de username en casos edge)."""
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
    """Crea un usuario con contraseña temporal; el flag `temp_password` fuerza cambio en el primer login."""
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
    """Actualiza el hash de la contraseña y desactiva el flag de contraseña temporal."""
    user = session.get(User, user_id)
    if not user:
        return None
    user.hashed_password = hashed_password
    user.temp_password = False
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def update_avatar(session: Session, user_id: int, avatar_icon: str) -> Optional[User]:
    """Guarda el nombre del icono FontAwesome elegido como avatar por el usuario."""
    user = session.get(User, user_id)
    if not user:
        return None
    user.avatar_icon = avatar_icon
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def delete_user(session: Session, user_id: int) -> bool:
    """Elimina un usuario; devuelve False si no existe."""
    user = session.get(User, user_id)
    if not user:
        return False
    session.delete(user)
    session.commit()
    return True


def get_user_by_id(session: Session, user_id: int) -> Optional[User]:
    """Recupera un usuario por su id numérico."""
    return session.get(User, user_id)


def delete_institution(session: Session, institution_id: int) -> bool:
    """Elimina una institución; devuelve False si no existe."""
    inst = session.get(Institution, institution_id)
    if not inst:
        return False
    session.delete(inst)
    session.commit()
    return True


# ── External Contacts ─────────────────────────────────────

def get_contacts(session: Session, institution_code: str) -> list[ExternalContact]:
    """Devuelve los contactos externos de una institución ordenados por fecha de creación."""
    return list(session.exec(
        select(ExternalContact)
        .where(ExternalContact.institution_code == institution_code)
        .order_by(ExternalContact.created_at.asc())
    ).all())


def create_contact(
    session: Session,
    institution_code: str,
    label: str,
    phone: str,
    notes: str,
    created_by: str,
) -> ExternalContact:
    """Agrega un nuevo contacto externo (policía, emergencias, etc.) a la institución."""
    c = ExternalContact(
        institution_code=institution_code,
        label=label, phone=phone, notes=notes, created_by=created_by,
    )
    session.add(c)
    session.commit()
    session.refresh(c)
    return c


def delete_contact(session: Session, contact_id: int, institution_code: str) -> bool:
    """Elimina un contacto; verifica que pertenece a la institución del usuario para evitar borrados cruzados."""
    c = session.get(ExternalContact, contact_id)
    if not c or c.institution_code != institution_code:
        return False
    session.delete(c)
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
    """Versión alternativa de save_incident usada en el flujo de análisis en dos pasos."""
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
