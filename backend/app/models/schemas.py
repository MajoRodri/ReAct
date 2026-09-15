from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from datetime import datetime


class UrgencyLevel(str, Enum):
    low      = "baja"
    medium   = "media"
    high     = "alta"
    critical = "crítica"


class IncidentCategory(str, Enum):
    bullying  = "acoso"
    violence  = "violencia_fisica"
    verbal    = "agresion_verbal"
    exclusion = "exclusion_social"
    substance = "sustancias"
    self_harm = "autolesion"
    other     = "otro"


class Department(str, Enum):
    tutoring   = "tutoria"
    counseling = "orientacion"
    management = "direccion"
    external   = "servicios_externos"


class TriageRequest(BaseModel):
    report_text:  str = Field(..., min_length=10, description="Texto del reporte")
    student_name: str = Field(default="")
    provider:     str = Field(default="ollama", pattern="^(ollama|groq)$")


class TriageResult(BaseModel):
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
    id:            int
    category:      str
    urgency_level: str
    summary:       str
    confirmed:     bool
    created_at:    datetime


class TriageResponse(BaseModel):
    success:         bool
    data:            Optional[TriageResult]    = None
    incident_id:     Optional[int]             = None
    student_history: list[IncidentSummary]     = []
    is_repeat:       bool                      = False
    error:           Optional[str]             = None


class CompareRequest(BaseModel):
    report_text:  str = Field(..., min_length=10)
    student_name: str = Field(default="")


class CompareResponse(BaseModel):
    ollama_result: Optional[TriageResult] = None
    groq_result:   Optional[TriageResult] = None
    ollama_error:  Optional[str]          = None
    groq_error:    Optional[str]          = None


class ConfirmResponse(BaseModel):
    success: bool
    message: str


class RedirectRequest(BaseModel):
    department:      Optional[Department]   = None
    urgency_level:   Optional[UrgencyLevel] = None
    redirect_reason: str                    = ""


class RedirectResponse(BaseModel):
    success:       bool
    message:       str
    department:    Optional[str] = None
    urgency_level: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    name:         str
    role:         str
    department:   Optional[str]


class FollowUpCreate(BaseModel):
    incident_id:    int
    scheduled_date: datetime
    notes:          str = ""


class FollowUpOut(BaseModel):
    id:             int
    incident_id:    int
    department:     str
    scheduled_date: datetime
    notes:          str
    created_by:     str
    created_at:     datetime


class RegisterRequest(BaseModel):
    first_name:       str = Field(..., min_length=2)
    last_name:        str = Field(..., min_length=2)
    email:            str = Field(..., min_length=5)
    institution_code: str = Field(..., min_length=4)
    department:       Department


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password:     str = Field(..., min_length=8)


class AnalyzeRequest(BaseModel):
    student_code: str = ""
    student_name: str = ""
    report_text:  str = Field(..., min_length=1)


class SaveIncidentRequest(BaseModel):
    student_code: str = ""
    student_name: str = ""
    report_text:  str
    result:       TriageResult


class InstitutionCreate(BaseModel):
    name: str = Field(..., min_length=3)


class InstitutionOut(BaseModel):
    id:         int
    name:       str
    code:       str
    created_at: datetime


class StudentOut(BaseModel):
    code:      str
    full_name: str
    grade:     str


class InviteAdminRequest(BaseModel):
    first_name: str = Field(..., min_length=2)
    last_name:  str = Field(..., min_length=2)
    email:      str = Field(..., min_length=5)


class UpdateNameRequest(BaseModel):
    first_name: str = Field(..., min_length=2)
    last_name:  str = Field(..., min_length=2)
