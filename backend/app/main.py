import secrets
import asyncio
import threading
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlmodel import Session
import os

from app.models.schemas import (
    TriageRequest, TriageResponse, TriageResult,
    CompareRequest, CompareResponse,
    IncidentSummary, ConfirmResponse,
    RedirectRequest, RedirectResponse,
    LoginRequest, TokenResponse,
    FollowUpCreate, FollowUpOut, FollowUpUpdate,
    ContactCreate, ContactOut,
    RegisterRequest, ChangePasswordRequest,
    AnalyzeRequest, SaveIncidentRequest,
    InstitutionCreate, InstitutionOut,
    InviteAdminRequest, UpdateNameRequest,
    StudentCreate, StudentOut,
    AvatarUpdateRequest,
)
from app.db.database import init_db, get_session
from app.db import repository as repo
from app.auth.auth import verify_password, hash_password, create_token
from app.auth.dependencies import get_current_user, require_admin

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

app = FastAPI(title="Motor de Triaje Escolar", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def on_startup():
    from app.core.config import settings
    print(f"[CONFIG] groq_model={settings.groq_model!r}  ollama_model={settings.ollama_model!r}", flush=True)
    init_db()


# ── Páginas ───────────────────────────────────────────────

@app.get("/", response_class=FileResponse)
def serve_app():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/login", response_class=FileResponse)
def serve_login():
    return FileResponse(os.path.join(STATIC_DIR, "login.html"))


# ── Auth ──────────────────────────────────────────────────

@app.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, session: Session = Depends(get_session)):
    # Try email first, then fall back to username
    user = repo.get_user_by_email(session, req.username)
    if not user:
        user = repo.get_user_by_username(session, req.username)
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    token = create_token(
        user.username,
        user.role,
        user.department,
        user.name,
        institution_code=user.institution_code,
        temp_password=user.temp_password,
    )
    return TokenResponse(
        access_token=token,
        name=user.name,
        role=user.role,
        department=user.department,
    )


@app.get("/auth/me")
def me(user: dict = Depends(get_current_user)):
    return user


@app.post("/auth/register")
async def register(req: RegisterRequest, session: Session = Depends(get_session)):
    # Validate institution
    institution = repo.get_institution_by_code(session, req.institution_code)
    if not institution:
        raise HTTPException(status_code=404, detail="Código de institución no válido")

    # Check email not taken
    existing = repo.get_user_by_email(session, req.email)
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo")

    # Derive role from department
    dept_role_map = {
        "tutoria":           "tutor",
        "orientacion":       "orientador",
        "direccion":         "director",
        "servicios_externos": "externo",
        "profesorado":       "profesor",
    }
    role = dept_role_map.get(req.department.value, "profesor")

    # Generate temporary password
    temp_pwd = secrets.token_urlsafe(10)
    hashed   = hash_password(temp_pwd)

    # Create user
    user = repo.create_user(
        session=session,
        email=req.email,
        first_name=req.first_name,
        last_name=req.last_name,
        role=role,
        department=req.department.value,
        institution_code=req.institution_code,
        hashed_password=hashed,
    )

    # Send email in background thread (non-blocking)
    def _send():
        from app.services.email_service import send_temp_password
        send_temp_password(
            to_email=req.email,
            name=f"{req.first_name} {req.last_name}".strip(),
            temp_password=temp_pwd,
            institution_name=institution.name,
        )

    asyncio.get_event_loop().create_task(asyncio.to_thread(_send))

    return {"message": "Cuenta creada. Hemos enviado tu contraseña temporal al correo indicado."}


@app.post("/auth/change-password", response_model=TokenResponse)
def change_password(
    req: ChangePasswordRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    user = repo.get_user_by_username(session, current_user["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not verify_password(req.current_password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Contraseña actual incorrecta")

    updated = repo.change_user_password(session, user.id, hash_password(req.new_password))
    token = create_token(
        updated.username,
        updated.role,
        updated.department,
        updated.name,
        institution_code=updated.institution_code,
        temp_password=False,
    )
    return TokenResponse(
        access_token=token,
        name=updated.name,
        role=updated.role,
        department=updated.department,
    )


# ── Profile ───────────────────────────────────────────────

@app.get("/profile")
def get_profile(
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    user = repo.get_user_by_username(session, current_user["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    institution_name = None
    if user.institution_code:
        inst = repo.get_institution_by_code(session, user.institution_code)
        institution_name = inst.name if inst else None

    return {
        "id":               user.id,
        "username":         user.username,
        "email":            user.email,
        "name":             user.name,
        "first_name":       user.first_name,
        "last_name":        user.last_name,
        "role":             user.role,
        "department":       user.department,
        "institution_code": user.institution_code,
        "institution_name": institution_name,
        "temp_password":    user.temp_password,
        "avatar_icon":      user.avatar_icon or "",
        "created_at":       user.created_at.isoformat() if user.created_at else None,
    }


@app.patch("/profile/name")
def update_profile_name(
    body: UpdateNameRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    user = repo.get_user_by_username(session, current_user["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.first_name = body.first_name.strip()
    user.last_name  = body.last_name.strip()
    user.name       = f"{body.first_name.strip()} {body.last_name.strip()}".strip()
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"name": user.name, "first_name": user.first_name, "last_name": user.last_name}


@app.delete("/profile")
def delete_profile(
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") == "admin":
        raise HTTPException(status_code=403, detail="El administrador no puede eliminar su propia cuenta desde aquí")
    user = repo.get_user_by_username(session, current_user["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    repo.delete_user(session, user.id)
    return {"message": "Cuenta eliminada correctamente"}


# ── Health ────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "triage-engine"}


# ── Triage ────────────────────────────────────────────────

@app.post("/triage", response_model=TriageResponse)
async def triage_incident(
    request: TriageRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
) -> TriageResponse:
    from app.services.triage_service import run_triage

    # solo profesores y admin pueden crear reportes
    if user["role"] not in ("profesor", "admin"):
        raise HTTPException(status_code=403, detail="Solo los profesores pueden crear reportes")

    history = repo.get_student_history(session, request.student_name)

    try:
        result: TriageResult = await run_triage(request.report_text, request.provider, history)
        incident = repo.save_incident(
            session, request.student_name, request.report_text, result, user["sub"]
        )
        history_out = [
            IncidentSummary(
                id=h.id,
                category=h.category,
                urgency_level=h.urgency_level,
                summary=h.summary,
                confirmed=h.confirmed,
                created_at=h.created_at,
            )
            for h in history
        ]
        return TriageResponse(
            success=True,
            data=result,
            incident_id=incident.id,
            student_history=history_out,
            is_repeat=len(history) > 0,
        )
    except Exception as e:
        return TriageResponse(success=False, error=str(e))


# ── Students ──────────────────────────────────────────────

@app.get("/students")
def list_students(
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    if user["role"] not in ("director", "admin"):
        raise HTTPException(status_code=403, detail="Solo dirección puede ver el listado de alumnos")
    return [{"code": s.code, "full_name": s.full_name} for s in repo.get_all_students(session)]


@app.post("/students", response_model=StudentOut)
def add_student(
    body: StudentCreate,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    if user["role"] not in ("director", "admin"):
        raise HTTPException(status_code=403, detail="Solo dirección puede registrar alumnos")
    existing = repo.get_student_by_code(session, body.code)
    if existing:
        raise HTTPException(status_code=409, detail=f"La matrícula {body.code} ya existe")
    inst = user.get("institution_code")
    student = repo.create_student(session, body.code, body.full_name, inst)
    return StudentOut(code=student.code, full_name=student.full_name)


@app.get("/students/{code}")
def lookup_student(
    code: str,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    student = repo.get_student_by_code(session, code)
    if not student:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")
    history = repo.get_student_history(session, student.code)
    return {
        "code":           student.code,
        "full_name":      student.full_name,
        "incident_count": len(history),
    }


# ── Analyze (no save) ─────────────────────────────────────

@app.post("/analyze")
async def analyze_incident(
    request: AnalyzeRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    from app.services.triage_service import run_triage

    if user["role"] not in ("profesor", "admin", "tutor", "orientador", "director", "externo"):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    history = repo.get_student_history(session, request.student_code)

    async def safe_triage(provider: str):
        try:
            return await run_triage(request.report_text, provider, history), None
        except Exception as e:
            return None, str(e)

    (ollama_res, ollama_err), (groq_res, groq_err) = await asyncio.gather(
        safe_triage("ollama"),
        safe_triage("groq"),
    )

    history_out = [
        {
            "id":            h.id,
            "category":      h.category,
            "urgency_level": h.urgency_level,
            "summary":       h.summary,
            "confirmed":     h.confirmed,
            "created_at":    h.created_at.isoformat(),
        }
        for h in history
    ]

    return {
        "ollama_result":    ollama_res,
        "groq_result":      groq_res,
        "ollama_error":     ollama_err,
        "groq_error":       groq_err,
        "is_repeat":        len(history) > 0,
        "student_history":  history_out,
    }


# ── Incidents ─────────────────────────────────────────────

@app.get("/incidents")
def list_incidents(
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    # admin ve todo; profesores ven sus propios reportes; departamentos ven los suyos
    if user["role"] == "admin":
        incidents = repo.get_all_incidents(session)
    elif user["role"] == "profesor":
        incidents = [i for i in repo.get_all_incidents(session) if i.reported_by == user["sub"]]
    else:
        incidents = repo.get_all_incidents(session, department=user["department"])

    return [
        {
            "id":              i.id,
            "student_name":    i.student_name,
            "category":        i.category,
            "urgency_level":   i.urgency_level,
            "department":      i.department,
            "summary":         i.summary,
            "confirmed":       i.confirmed,
            "reported_by":     i.reported_by,
            "created_at":      i.created_at.isoformat(),
            "redirected_by":   i.redirected_by,
            "redirect_reason": i.redirect_reason,
        }
        for i in incidents
    ]


@app.post("/incidents/save", response_model=TriageResponse)
def save_incident_endpoint(
    body: SaveIncidentRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    if user["role"] not in ("profesor", "admin", "tutor", "orientador", "director", "externo"):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    history = repo.get_student_history(session, body.student_code)

    try:
        incident = repo.save_incident_from_result(
            session, body.student_name, body.report_text, body.result, user["sub"],
            student_code=body.student_code,
        )
        history_out = [
            IncidentSummary(
                id=h.id,
                category=h.category,
                urgency_level=h.urgency_level,
                summary=h.summary,
                confirmed=h.confirmed,
                created_at=h.created_at,
            )
            for h in history
        ]
        return TriageResponse(
            success=True,
            data=body.result,
            incident_id=incident.id,
            student_history=history_out,
            is_repeat=len(history) > 0,
        )
    except Exception as e:
        return TriageResponse(success=False, error=str(e))


@app.patch("/incidents/{incident_id}/confirm", response_model=ConfirmResponse)
def confirm_incident(
    incident_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    if user["role"] == "profesor":
        raise HTTPException(status_code=403, detail="Los profesores no pueden confirmar incidencias")
    incident = repo.confirm_incident(session, incident_id, confirmed_by=user.get("name", user["sub"]))
    if not incident:
        return ConfirmResponse(success=False, message="Incidencia no encontrada")
    return ConfirmResponse(success=True, message="Incidencia confirmada y registrada")


@app.patch("/incidents/{incident_id}/redirect", response_model=RedirectResponse)
def redirect_incident(
    incident_id: int,
    body: RedirectRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    if user["role"] == "profesor":
        raise HTTPException(status_code=403, detail="Los profesores no pueden redirigir incidencias")
    if not body.department and not body.urgency_level:
        raise HTTPException(status_code=422, detail="Indica al menos un nuevo departamento o nivel de urgencia")

    dept    = body.department.value    if body.department    else None
    urgency = body.urgency_level.value if body.urgency_level else None

    incident = repo.redirect_incident(
        session, incident_id,
        department=dept,
        urgency_level=urgency,
        redirect_reason=body.redirect_reason,
        redirected_by=user["sub"],
    )
    if not incident:
        return RedirectResponse(success=False, message="Incidencia no encontrada")
    return RedirectResponse(
        success=True,
        message="Incidencia redirigida correctamente",
        department=incident.department,
        urgency_level=incident.urgency_level,
    )


@app.patch("/profile/avatar")
def update_avatar(
    body: AvatarUpdateRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    db_user = repo.get_user_by_username(session, user["sub"])
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    updated = repo.update_avatar(session, db_user.id, body.avatar_icon)
    return {"avatar_icon": updated.avatar_icon}


# ── Calendar ──────────────────────────────────────────────

@app.get("/calendar")
def get_calendar(
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    from app.db.models import Incident
    dept = None if user["role"] == "admin" else user["department"]
    fus  = repo.get_followups_by_department(session, dept)
    result = []
    for f in fus:
        inc = session.get(Incident, f.incident_id)
        result.append({
            "id":                 f.id,
            "incident_id":        f.incident_id,
            "department":         f.department,
            "scheduled_date":     f.scheduled_date.isoformat(),
            "notes":              f.notes,
            "created_by":         f.created_by,
            "created_at":         f.created_at.isoformat(),
            "urgency_level":      inc.urgency_level if inc else "baja",
            "incident_confirmed": inc.confirmed     if inc else False,
            "confirmed_by":       inc.confirmed_by  if inc else None,
            "student_name":       inc.student_name  if inc else "",
        })
    return result


@app.post("/calendar")
def create_followup(
    body: FollowUpCreate,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    from app.db.models import Incident
    if user["role"] == "profesor":
        raise HTTPException(status_code=403, detail="Los profesores no pueden agendar seguimientos")
    dept = user["department"] if user["role"] != "admin" else "admin"
    inc  = session.get(Incident, body.incident_id)
    urgency = inc.urgency_level if inc else "baja"
    fu = repo.save_followup(
        session,
        body.incident_id,
        dept,
        body.scheduled_date,
        body.notes,
        user["sub"],
        urgency_level=urgency,
    )
    return {
        "id": fu.id, "incident_id": fu.incident_id, "department": fu.department,
        "scheduled_date": fu.scheduled_date.isoformat(), "notes": fu.notes,
        "created_by": fu.created_by, "created_at": fu.created_at.isoformat(),
        "urgency_level": fu.urgency_level, "incident_confirmed": False, "student_name": "",
    }


@app.patch("/calendar/{followup_id}")
def update_followup(
    followup_id: int,
    body: FollowUpUpdate,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    if user["role"] == "profesor":
        raise HTTPException(status_code=403, detail="Sin permiso")
    fu = repo.update_followup(session, followup_id, body.scheduled_date, body.notes)
    if not fu:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    from app.db.models import Incident
    inc = session.get(Incident, fu.incident_id)
    return {
        "id": fu.id, "incident_id": fu.incident_id, "department": fu.department,
        "scheduled_date": fu.scheduled_date.isoformat(), "notes": fu.notes,
        "created_by": fu.created_by, "created_at": fu.created_at.isoformat(),
        "urgency_level": inc.urgency_level if inc else fu.urgency_level,
        "incident_confirmed": inc.confirmed  if inc else False,
        "confirmed_by":       inc.confirmed_by if inc else None,
        "student_name": inc.student_name if inc else "",
    }


# ── External Contacts ─────────────────────────────────────

@app.get("/contacts", response_model=list[ContactOut])
def get_contacts(
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    inst = user.get("institution_code")
    if not inst:
        raise HTTPException(status_code=403, detail="Sin institución asignada")
    return repo.get_contacts(session, inst)


@app.post("/contacts", response_model=ContactOut, status_code=201)
def add_contact(
    body: ContactCreate,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    if user.get("department") != "servicios_externos" and user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo servicios externos puede gestionar contactos")
    inst = user.get("institution_code")
    if not inst:
        raise HTTPException(status_code=403, detail="Sin institución asignada")
    return repo.create_contact(session, inst, body.label, body.phone, body.notes, user.get("name", user["sub"]))


@app.delete("/contacts/{contact_id}", status_code=204)
def delete_contact(
    contact_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    if user.get("department") != "servicios_externos" and user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Sin permiso")
    inst = user.get("institution_code") or ""
    if not repo.delete_contact(session, contact_id, inst):
        raise HTTPException(status_code=404, detail="Contacto no encontrado")


# ── Compare ───────────────────────────────────────────────

@app.post("/compare", response_model=CompareResponse)
async def compare_providers(
    request: CompareRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
) -> CompareResponse:
    from app.services.triage_service import run_triage

    if user["role"] not in ("profesor", "admin"):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    history = repo.get_student_history(session, request.student_name)

    async def safe_triage(provider: str):
        try:
            return await run_triage(request.report_text, provider, history), None
        except Exception as e:
            return None, str(e)

    (ollama_res, ollama_err), (groq_res, groq_err) = await asyncio.gather(
        safe_triage("ollama"),
        safe_triage("groq"),
    )

    return CompareResponse(
        ollama_result=ollama_res,
        groq_result=groq_res,
        ollama_error=ollama_err,
        groq_error=groq_err,
    )


# ── Institutions ──────────────────────────────────────────

@app.get("/institutions", response_model=list[InstitutionOut])
def list_institutions(
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin),
):
    institutions = repo.get_all_institutions(session)
    return [
        InstitutionOut(
            id=i.id,
            name=i.name,
            code=i.code,
            created_at=i.created_at,
        )
        for i in institutions
    ]


@app.post("/institutions", response_model=InstitutionOut)
def create_institution(
    body: InstitutionCreate,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin),
):
    institution = repo.create_institution(session, body.name)
    return InstitutionOut(
        id=institution.id,
        name=institution.name,
        code=institution.code,
        created_at=institution.created_at,
    )


@app.delete("/institutions/{institution_id}")
def delete_institution(
    institution_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin),
):
    ok = repo.delete_institution(session, institution_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Institución no encontrada")
    return {"message": "Institución eliminada correctamente"}


# ── Admin user management ─────────────────────────────────

@app.get("/admin/users")
def list_all_users(
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin),
):
    users = repo.get_all_users(session)
    result = []
    for u in users:
        inst_name = None
        if u.institution_code:
            inst = repo.get_institution_by_code(session, u.institution_code)
            inst_name = inst.name if inst else None
        result.append({
            "id":               u.id,
            "username":         u.username,
            "name":             u.name,
            "email":            u.email,
            "role":             u.role,
            "department":       u.department,
            "institution_code": u.institution_code,
            "institution_name": inst_name,
            "temp_password":    u.temp_password,
            "created_at":       u.created_at.isoformat() if u.created_at else None,
        })
    return result


@app.post("/admin/create-admin")
async def invite_admin(
    body: InviteAdminRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(require_admin),
):
    existing = repo.get_user_by_email(session, body.email)
    temp_pwd = secrets.token_urlsafe(10)

    if existing:
        if existing.role != "admin":
            raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo para otro rol")
        # Admin account already exists - reissue temp password and resend invitation
        existing.hashed_password = hash_password(temp_pwd)
        existing.temp_password = True
        session.add(existing)
        session.commit()
        display_name = f"{existing.first_name} {existing.last_name}".strip() or existing.email
    else:
        repo.create_user(
            session=session,
            email=body.email,
            first_name=body.first_name,
            last_name=body.last_name,
            role="admin",
            department=None,
            institution_code=None,
            hashed_password=hash_password(temp_pwd),
        )
        display_name = f"{body.first_name} {body.last_name}".strip()

    def _send():
        from app.services.email_service import send_temp_password
        send_temp_password(
            to_email=body.email,
            name=display_name,
            temp_password=temp_pwd,
            institution_name="Sistema de Triaje Escolar (Administrador)",
        )

    asyncio.get_event_loop().create_task(asyncio.to_thread(_send))
    return {"message": f"Invitación enviada a {body.email}"}


@app.delete("/admin/users/{user_id}")
def admin_delete_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: dict = Depends(require_admin),
):
    target = repo.get_user_by_id(session, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if target.role == "admin":
        raise HTTPException(status_code=403, detail="No se puede eliminar a otro administrador")
    if target.username == current_user["sub"]:
        raise HTTPException(status_code=403, detail="Usa 'Eliminar cuenta' en tu perfil")
    repo.delete_user(session, user_id)
    return {"message": "Usuario eliminado correctamente"}
