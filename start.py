import subprocess
import sys
import os
import time
import signal
from pathlib import Path

ROOT = Path(__file__).parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"


def main():
    procs = []

    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"],
        cwd=BACKEND_DIR,
    )
    procs.append(backend)

    time.sleep(2)

    frontend = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501"],
        cwd=FRONTEND_DIR,
    )
    procs.append(frontend)
    print("✅ Frontend starting at http://localhost:8501")
    print("\nPress Ctrl+C to stop both servers.\n")

    def shutdown(sig, frame):
        print("\nShutting down...")
        for p in procs:
            p.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    while True:
        for p in procs:
            ret = p.poll()
            if ret is not None:
                print(f"Process {p.args[0]} exited with code {ret}. Shutting down.")
                shutdown(None, None)
        time.sleep(1)


if __name__ == "__main__":
    main()
