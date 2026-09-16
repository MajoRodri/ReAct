import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_USER     = os.getenv("GMAIL_USER", "")
GMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")


def send_temp_password(to_email: str, name: str, temp_password: str, institution_name: str):
    if not GMAIL_USER or not GMAIL_PASSWORD:
        print(f"[EMAIL] No config - temp pwd for {to_email}: {temp_password}")
        return
    subject = "Tu acceso al Motor de Triaje Escolar"
    body = f"""Hola, {name}.

Tu cuenta ha sido creada en el Motor de Triaje Escolar
Institución: {institution_name}

Credenciales:
  Correo: {to_email}
  Contraseña temporal: {temp_password}

Accede en: http://localhost:8000
Recuerda cambiar tu contraseña después del primer acceso.

Motor de Triaje Escolar"""
    msg = MIMEMultipart()
    msg["From"]    = GMAIL_USER
    msg["To"]      = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(GMAIL_USER, GMAIL_PASSWORD)
            smtp.sendmail(GMAIL_USER, to_email, msg.as_string())
        print(f"[EMAIL] Sent to {to_email}")
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
