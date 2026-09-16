import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from sqlmodel import create_engine, SQLModel, Session, select

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "triage.db")
engine  = create_engine(f"sqlite:///{DB_PATH}", echo=False)

# usuarios iniciales del sistema
DEMO_INSTITUTION = {"name": "Centro Educativo Demo", "code": "DEMO0001"}

INITIAL_USERS = [
    {
        "username": "admin",
        "password": "admin123",
        "name": "Admin Sistema",
        "role": "admin",
        "department": None,
        "email": "admin@cedemo.es",
        "first_name": "Admin",
        "last_name": "Sistema",
        "institution_code": None,
        "temp_password": False,
    },
    {
        "username": "javier",
        "password": "javier123",
        "name": "Javier Moreno",
        "role": "orientador",
        "department": "orientacion",
        "email": "javier.moreno@cedemo.es",
        "first_name": "Javier",
        "last_name": "Moreno",
        "institution_code": "DEMO0001",
        "temp_password": False,
    },
    {
        "username": "marta",
        "password": "marta123",
        "name": "Marta Sánchez",
        "role": "orientador",
        "department": "orientacion",
        "email": "marta.sanchez@cedemo.es",
        "first_name": "Marta",
        "last_name": "Sánchez",
        "institution_code": "DEMO0001",
        "temp_password": False,
    },
    {
        "username": "garcia",
        "password": "garcia123",
        "name": "Carlos García",
        "role": "profesor",
        "department": "profesorado",
        "email": "carlos.garcia@cedemo.es",
        "first_name": "Carlos",
        "last_name": "García",
        "institution_code": "DEMO0001",
        "temp_password": False,
    },
    {
        "username": "lopez",
        "password": "lopez123",
        "name": "María López",
        "role": "profesor",
        "department": "profesorado",
        "email": "maria.lopez@cedemo.es",
        "first_name": "María",
        "last_name": "López",
        "institution_code": "DEMO0001",
        "temp_password": False,
    },
    {
        "username": "tutoria",
        "password": "tut123",
        "name": "Laura Martínez",
        "role": "tutor",
        "department": "tutoria",
        "email": "laura.martinez@cedemo.es",
        "first_name": "Laura",
        "last_name": "Martínez",
        "institution_code": "DEMO0001",
        "temp_password": False,
    },
    {
        "username": "direccion",
        "password": "dir123",
        "name": "Carlos Ruiz",
        "role": "director",
        "department": "direccion",
        "email": "carlos.ruiz@cedemo.es",
        "first_name": "Carlos",
        "last_name": "Ruiz",
        "institution_code": "DEMO0001",
        "temp_password": False,
    },
    {
        "username": "externos",
        "password": "ext123",
        "name": "Ana Torres",
        "role": "externo",
        "department": "servicios_externos",
        "email": "ana.torres@cedemo.es",
        "first_name": "Ana",
        "last_name": "Torres",
        "institution_code": "DEMO0001",
        "temp_password": False,
    },
]


DEMO_STUDENTS = [
    {"code": "EST2026001", "full_name": "Lucía Fernández Torres",    "grade": "1º ESO A"},
    {"code": "EST2026002", "full_name": "Miguel Ángel Ramírez",      "grade": "1º ESO B"},
    {"code": "EST2026003", "full_name": "Sofía Martínez García",     "grade": "2º ESO A"},
    {"code": "EST2026004", "full_name": "Carlos Jiménez Soto",       "grade": "2º ESO B"},
    {"code": "EST2026005", "full_name": "Ana Belén Ruiz Moreno",     "grade": "3º ESO A"},
    {"code": "EST2026006", "full_name": "Pablo González Herrera",    "grade": "3º ESO B"},
    {"code": "EST2026007", "full_name": "Elena Sánchez Ortega",      "grade": "4º ESO A"},
    {"code": "EST2026008", "full_name": "Javier López Vega",         "grade": "4º ESO B"},
    {"code": "EST2026009", "full_name": "María Carmen Castro Díaz",  "grade": "1º BACH A"},
    {"code": "EST2026010", "full_name": "Alejandro Torres Blanco",   "grade": "1º BACH B"},
]


def init_db():
    from app.db.models import User, Incident, FollowUp, Institution, ExternalContact  # noqa: evita import circular
    from app.auth.auth import hash_password
    from sqlalchemy import text

    SQLModel.metadata.create_all(engine)

    # migración segura: agrega columnas nuevas si no existen
    with engine.connect() as conn:
        # Incident columns
        incident_columns = [
            ("reported_by",    "TEXT"),
            ("created_at",     "DATETIME"),
            ("redirected_by",  "TEXT"),
            ("redirect_reason","TEXT"),
            ("student_code",   "TEXT"),
            ("confirmed_by",   "TEXT"),
        ]
        for col, typedef in incident_columns:
            try:
                conn.execute(text(f'ALTER TABLE incident ADD COLUMN {col} {typedef}'))
            except Exception:
                pass

        # User columns
        user_columns = [
            ("email",            "TEXT NOT NULL DEFAULT ''"),
            ("first_name",       "TEXT NOT NULL DEFAULT ''"),
            ("last_name",        "TEXT NOT NULL DEFAULT ''"),
            ("institution_code", "TEXT"),
            ("temp_password",    "INTEGER NOT NULL DEFAULT 0"),
            ("avatar_icon",      "TEXT"),
            ("created_at",       "DATETIME"),
        ]
        for col, typedef in user_columns:
            try:
                conn.execute(text(f'ALTER TABLE "user" ADD COLUMN {col} {typedef}'))
            except Exception:
                pass

        # FollowUp urgency_level column
        try:
            conn.execute(text("ALTER TABLE followup ADD COLUMN urgency_level TEXT NOT NULL DEFAULT 'baja'"))
        except Exception:
            pass

        conn.commit()

    # After User migration, fill email from username for existing rows
    with engine.connect() as conn:
        conn.execute(text("UPDATE \"user\" SET email = username WHERE email = '' OR email IS NULL"))

        # Fix demo user names and emails
        demo_names = [
            ("admin",     "Admin",  "Sistema",  "Admin Sistema",  "admin@cedemo.es"),
            ("javier",    "Javier", "Moreno",   "Javier Moreno",  "javier.moreno@cedemo.es"),
            ("marta",     "Marta",  "Sánchez",  "Marta Sánchez",  "marta.sanchez@cedemo.es"),
            ("garcia",    "Carlos", "García",   "Carlos García",  "carlos.garcia@cedemo.es"),
            ("lopez",     "María",  "López",    "María López",    "maria.lopez@cedemo.es"),
            ("tutoria",   "Laura",  "Martínez", "Laura Martínez", "laura.martinez@cedemo.es"),
            ("direccion", "Carlos", "Ruiz",     "Carlos Ruiz",    "carlos.ruiz@cedemo.es"),
            ("externos",  "Ana",    "Torres",   "Ana Torres",     "ana.torres@cedemo.es"),
        ]
        for username, fn, ln, full, email in demo_names:
            conn.execute(text(
                "UPDATE \"user\" SET first_name=:fn, last_name=:ln, name=:full, email=:email "
                "WHERE username=:u"
            ), {"fn": fn, "ln": ln, "full": full, "email": email, "u": username})

        # Assign demo institution to all non-admin demo users that have no institution
        demo_usernames = ("javier","marta","garcia","lopez","tutoria","direccion","externos")
        for u in demo_usernames:
            conn.execute(text(
                "UPDATE \"user\" SET institution_code='DEMO0001' "
                "WHERE username=:u AND (institution_code IS NULL OR institution_code='')"
            ), {"u": u})

        conn.commit()

    with Session(engine) as session:
        # Ensure the demo institution exists
        from app.db.models import Institution
        demo_inst = session.exec(select(Institution).where(Institution.code == DEMO_INSTITUTION["code"])).first()
        if not demo_inst:
            session.add(Institution(name=DEMO_INSTITUTION["name"], code=DEMO_INSTITUTION["code"]))
            session.commit()

        for u in INITIAL_USERS:
            exists = session.exec(select(User).where(User.username == u["username"])).first()
            if not exists:
                session.add(User(
                    username=u["username"],
                    hashed_password=hash_password(u["password"]),
                    name=u["name"],
                    role=u["role"],
                    department=u["department"],
                    email=u["email"],
                    first_name=u["first_name"],
                    last_name=u["last_name"],
                    institution_code=u["institution_code"],
                    temp_password=u["temp_password"],
                ))
        session.commit()

    with Session(engine) as session:
        from app.db.models import Student
        for s in DEMO_STUDENTS:
            exists = session.exec(select(Student).where(Student.code == s["code"])).first()
            if not exists:
                session.add(Student(
                    code=s["code"],
                    full_name=s["full_name"],
                    grade=s["grade"],
                    institution_code="DEMO0001",
                ))
        session.commit()


def get_session():
    with Session(engine) as session:
        yield session
