"""Schemas Pydantic v2 para validación de requests/responses de la API.

Separa la lógica de dominio (models.py) de la capa de transporte HTTP,
garantizando que datos inválidos del cliente nunca lleguen a la BD.
"""

from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from datetime import datetime


# ── Enumerados de dominio ─────────────────────────────────

class UrgencyLevel(str, Enum):
    """Nivel de urgencia asignado por el LLM al incidente."""

    low      = "baja"
    medium   = "media"
    high     = "alta"
    critical = "crítica"


class IncidentCategory(str, Enum):
    """Tipo de incidente reconocido por el sistema de triaje."""

    bullying  = "acoso"
    violence  = "violencia_fisica"
    verbal    = "agresion_verbal"
    exclusion = "exclusion_social"
    substance = "sustancias"
    self_harm = "autolesion"
    other     = "otro"


class Department(str, Enum):
    """Departamento escolar al que se deriva el incidente."""

    tutoring   = "tutoria"
    counseling = "orientacion"
    management = "direccion"
    external   = "servicios_externos"


# ── Triaje ────────────────────────────────────────────────

class TriageRequest(BaseModel):
    """Datos mínimos que el cliente envía para iniciar un triaje."""

    report_text:  str = Field(..., min_length=10, description="Texto del reporte")
    student_name: str = Field(default="")
    provider:     str = Field(default="ollama", pattern="^(ollama|groq)$")


class TriageResult(BaseModel):
    """Salida validada del LLM; Pydantic rechaza cualquier campo fuera del schema."""

    category:            IncidentCategory
    urgency_level:       UrgencyLevel
    department:          Department
    summary:             str = Field(..., description="Resumen en máximo 10 palabras")
    reasoning:           str = Field(..., description="Razonamiento CoT del modelo")
    provider:            str
    model:               str
    latency_ms:          float
    tokens_used:         Optional[int]   = None
    estimated_cost_usd:  Optional[float] = None


class IncidentSummary(BaseModel):
    """Versión reducida de un Incident para mostrar en el historial del estudiante."""

    id:            int
    category:      str
    urgency_level: str
    summary:       str
    confirmed:     bool
    created_at:    datetime


class TriageResponse(BaseModel):
    """Respuesta completa del endpoint POST /triage, incluyendo historial de reincidencia."""

    success:         bool
    data:            Optional[TriageResult]    = None
    incident_id:     Optional[int]             = None
    student_history: list[IncidentSummary]     = []
    is_repeat:       bool                      = False  # True si el estudiante tiene incidentes previos
    error:           Optional[str]             = None


class CompareRequest(BaseModel):
    """Petición para ejecutar el mismo reporte en ambos proveedores simultáneamente."""

    report_text:  str = Field(..., min_length=10)
    student_name: str = Field(default="")


class CompareResponse(BaseModel):
    """Resultados paralelos de Ollama y Groq; un campo puede ser None si falló ese proveedor."""

    ollama_result: Optional[TriageResult] = None
    groq_result:   Optional[TriageResult] = None
    ollama_error:  Optional[str]          = None
    groq_error:    Optional[str]          = None


# ── Confirmación y redirección ────────────────────────────

class ConfirmResponse(BaseModel):
    """Respuesta simple de éxito/fallo al confirmar un incidente."""

    success: bool
    message: str


class RedirectRequest(BaseModel):
    """Permite cambiar el departamento o urgencia de un incidente ya clasificado."""

    department:      Optional[Department]   = None
    urgency_level:   Optional[UrgencyLevel] = None
    redirect_reason: str                    = ""


class RedirectResponse(BaseModel):
    """Devuelve los valores actualizados tras redirigir un incidente."""

    success:       bool
    message:       str
    department:    Optional[str] = None
    urgency_level: Optional[str] = None


# ── Autenticación ─────────────────────────────────────────

class LoginRequest(BaseModel):
    """Credenciales para el endpoint POST /auth/login."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT y metadatos de sesión devueltos al cliente tras el login."""

    access_token: str
    token_type:   str = "bearer"
    name:         str
    role:         str
    department:   Optional[str]


# ── Seguimientos (citas) ──────────────────────────────────

class FollowUpCreate(BaseModel):
    """Datos para agendar una nueva cita de seguimiento."""

    incident_id:    int
    scheduled_date: datetime
    notes:          str = ""


class FollowUpUpdate(BaseModel):
    """Datos para editar fecha/hora y notas de una cita existente."""

    scheduled_date: datetime
    notes:          str = ""


class FollowUpOut(BaseModel):
    """Cita enriquecida con datos del incidente asociado para la vista de calendario."""

    id:                 int
    incident_id:        int
    department:         str
    scheduled_date:     datetime
    notes:              str
    created_by:         str
    created_at:         datetime
    urgency_level:      str  = "baja"
    incident_confirmed: bool = False
    student_name:       str  = ""


# ── Registro y gestión de usuarios ───────────────────────

class RegisterRequest(BaseModel):
    """Datos requeridos para que un nuevo profesional se registre con código de institución."""

    first_name:       str = Field(..., min_length=2)
    last_name:        str = Field(..., min_length=2)
    email:            str = Field(..., min_length=5)
    institution_code: str = Field(..., min_length=4)
    department:       Department


class ChangePasswordRequest(BaseModel):
    """Petición de cambio de contraseña; requiere la clave actual para evitar secuestro de sesión."""

    current_password: str
    new_password:     str = Field(..., min_length=8)


class AnalyzeRequest(BaseModel):
    """Petición de análisis sin guardar; usada en el flujo de triaje en dos pasos."""

    student_code: str = ""
    student_name: str = ""
    report_text:  str = Field(..., min_length=1)


class SaveIncidentRequest(BaseModel):
    """Guarda un TriageResult previamente calculado, separando análisis de persistencia."""

    student_code: str = ""
    student_name: str = ""
    report_text:  str
    result:       TriageResult


# ── Instituciones y estudiantes ───────────────────────────

class InstitutionCreate(BaseModel):
    """Nombre del centro educativo para crear una nueva institución."""

    name: str = Field(..., min_length=3)


class InstitutionOut(BaseModel):
    """Institución serializada para respuestas de la API."""

    id:         int
    name:       str
    code:       str
    created_at: datetime


class StudentOut(BaseModel):
    """Datos públicos de un estudiante (sin datos sensibles)."""

    code:      str
    full_name: str


class StudentCreate(BaseModel):
    """Datos mínimos para registrar un estudiante en el sistema."""

    code:      str = Field(..., min_length=3)
    full_name: str = Field(..., min_length=2)


# ── Administración ────────────────────────────────────────

class InviteAdminRequest(BaseModel):
    """Datos para que un super-admin invite a un nuevo administrador de institución."""

    first_name: str = Field(..., min_length=2)
    last_name:  str = Field(..., min_length=2)
    email:      str = Field(..., min_length=5)


class UpdateNameRequest(BaseModel):
    """Permite a un usuario actualizar su nombre y apellido desde el perfil."""

    first_name: str = Field(..., min_length=2)
    last_name:  str = Field(..., min_length=2)


# ── Contactos externos y avatar ───────────────────────────

class ContactCreate(BaseModel):
    """Datos para agregar un contacto externo (policía, emergencias…) a la institución."""

    label: str = Field(..., min_length=2)
    phone: str = Field(..., min_length=3)
    notes: str = ""


class ContactOut(BaseModel):
    """Contacto externo serializado para la vista de perfil de servicios externos."""

    id:         int
    label:      str
    phone:      str
    notes:      str
    created_by: str
    created_at: datetime


class AvatarUpdateRequest(BaseModel):
    """Nombre del icono FontAwesome seleccionado como avatar por el usuario."""

    avatar_icon: str = Field(..., min_length=3)
