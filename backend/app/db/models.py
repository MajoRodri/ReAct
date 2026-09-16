"""Modelos ORM de SQLModel que mapean directamente a tablas SQLite."""

from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class Institution(SQLModel, table=True):
    """Centro educativo que agrupa usuarios y estudiantes."""

    id:         Optional[int] = Field(default=None, primary_key=True)
    name:       str
    code:       str           = Field(unique=True, index=True)  # clave de acceso para registro
    created_at: datetime      = Field(default_factory=datetime.utcnow)


class Student(SQLModel, table=True):
    """Alumno registrado; su `code` se usa para ligar incidentes y consultar historial."""

    id:               Optional[int] = Field(default=None, primary_key=True)
    code:             str           = Field(unique=True, index=True)
    full_name:        str
    grade:            str
    institution_code: Optional[str] = None
    created_at:       datetime      = Field(default_factory=datetime.utcnow)


class User(SQLModel, table=True):
    """Cuenta de usuario del sistema; `role` determina permisos y vista en el dashboard."""

    id:               Optional[int]  = Field(default=None, primary_key=True)
    username:         str            = Field(unique=True, index=True)
    hashed_password:  str
    name:             str
    role:             str            # admin | profesor | tutor | orientador | director | externo
    department:       Optional[str]  = None  # None solo para admin
    email:            str            = Field(default="", index=True)
    first_name:       str            = Field(default="")
    last_name:        str            = Field(default="")
    institution_code: Optional[str]  = Field(default=None)
    temp_password:    bool           = Field(default=False)  # fuerza cambio de clave en primer login
    avatar_icon:      Optional[str]  = None  # nombre de icono FontAwesome seleccionado por el usuario
    created_at:       datetime       = Field(default_factory=datetime.utcnow)


class Incident(SQLModel, table=True):
    """Incidente de triaje: almacena el reporte, la clasificación del LLM y las métricas de inferencia."""

    id:                  Optional[int]   = Field(default=None, primary_key=True)
    student_name:        str             = Field(index=True)
    student_code:        Optional[str]   = Field(default=None, index=True)
    report_text:         str
    category:            str             # valor del enum IncidentCategory
    urgency_level:       str             # valor del enum UrgencyLevel
    department:          str             # departamento al que se asigna
    summary:             str             # resumen en ≤10 palabras generado por el LLM
    reasoning:           str             # cadena CoT: Observo → Pienso → Clasifico
    provider:            str             # 'ollama' | 'groq'
    model_name:          str
    latency_ms:          float
    tokens_used:         Optional[int]   = None
    estimated_cost_usd:  Optional[float] = None
    confirmed:           bool            = Field(default=False)
    confirmed_by:        Optional[str]   = None  # nombre del profesional que confirmó
    reported_by:         Optional[str]   = None  # usuario que registró el incidente
    created_at:          datetime        = Field(default_factory=datetime.utcnow)
    redirected_by:       Optional[str]   = None
    redirect_reason:     Optional[str]   = None


class ExternalContact(SQLModel, table=True):
    """Contacto externo (policía, emergencias, salud mental…) vinculado a una institución."""

    id:               Optional[int] = Field(default=None, primary_key=True)
    institution_code: str
    label:            str           # nombre descriptivo, ej. "Policía Nacional"
    phone:            str
    notes:            str           = ""
    created_by:       str
    created_at:       datetime      = Field(default_factory=datetime.utcnow)


class FollowUp(SQLModel, table=True):
    """Cita de seguimiento programada para un incidente confirmado."""

    id:             Optional[int] = Field(default=None, primary_key=True)
    incident_id:    int           # FK lógica al Incident relacionado
    department:     str
    scheduled_date: datetime
    notes:          str           = ""
    created_by:     str
    created_at:     datetime      = Field(default_factory=datetime.utcnow)
    urgency_level:  str           = Field(default="baja")
