from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class Institution(SQLModel, table=True):
    id:         Optional[int] = Field(default=None, primary_key=True)
    name:       str
    code:       str           = Field(unique=True, index=True)
    created_at: datetime      = Field(default_factory=datetime.utcnow)


class Student(SQLModel, table=True):
    id:               Optional[int] = Field(default=None, primary_key=True)
    code:             str           = Field(unique=True, index=True)
    full_name:        str
    grade:            str
    institution_code: Optional[str] = None
    created_at:       datetime      = Field(default_factory=datetime.utcnow)


class User(SQLModel, table=True):
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
    temp_password:    bool           = Field(default=False)
    created_at:       datetime       = Field(default_factory=datetime.utcnow)


class Incident(SQLModel, table=True):
    id:                  Optional[int]   = Field(default=None, primary_key=True)
    student_name:        str             = Field(index=True)
    student_code:        Optional[str]   = Field(default=None, index=True)
    report_text:         str
    category:            str
    urgency_level:       str
    department:          str
    summary:             str
    reasoning:           str
    provider:            str
    model_name:          str
    latency_ms:          float
    tokens_used:         Optional[int]   = None
    estimated_cost_usd:  Optional[float] = None
    confirmed:           bool            = Field(default=False)
    reported_by:         Optional[str]   = None
    created_at:          datetime        = Field(default_factory=datetime.utcnow)
    redirected_by:       Optional[str]   = None
    redirect_reason:     Optional[str]   = None


class FollowUp(SQLModel, table=True):
    id:             Optional[int] = Field(default=None, primary_key=True)
    incident_id:    int
    department:     str
    scheduled_date: datetime
    notes:          str           = ""
    created_by:     str
    created_at:     datetime      = Field(default_factory=datetime.utcnow)
    urgency_level:  str           = Field(default="baja")
