import subprocess
import sys
import signal
import os
import webbrowser
import time

BASE = os.path.dirname(__file__)

# Use the Python that's running this script (works with venv, conda, system Python)
PYTHON = sys.executable

processes = []

def shutdown(sig=None, frame=None):
    print("\nDeteniendo servidor...")
    for p in processes:
        p.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

backend = subprocess.Popen(
    [PYTHON, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
    cwd=os.path.join(BASE, "backend"),
)

processes = [backend]
time.sleep(2)

print("App corriendo en → http://localhost:8000")
print("Ctrl+C para detener.\n")
webbrowser.open("http://localhost:8000")

backend.wait()
