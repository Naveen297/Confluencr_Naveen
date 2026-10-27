#!/usr/bin/env python3
"""Runs the Transaction Ledger (API + web app) on a single port.

    python run.py            set up on first run, start the server, open the browser
    python run.py --seed     add demo accounts if the database is empty
    python run.py --dev      hot reload for backend and frontend
    python run.py --test     run the backend tests
    python run.py --reset    delete the local database
"""
import argparse
import hashlib
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
VENV = ROOT / ".venv"
DB_FILE = ROOT / "data" / "ledger.db"

IS_WINDOWS = os.name == "nt"
VENV_PYTHON = VENV / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")


def say(message: str) -> None:
    print(f"\033[1;34m›\033[0m {message}" if sys.stdout.isatty() else f"> {message}", flush=True)


def fail(message: str) -> None:
    print(f"\n  {message}\n", file=sys.stderr)
    sys.exit(1)


def in_project_venv() -> bool:
    return Path(sys.prefix).resolve() == VENV.resolve()


def ensure_python_env(with_dev: bool) -> None:
    if sys.version_info < (3, 9):
        fail(
            f"Python 3.9 or newer is required (found {sys.version.split()[0]}).\n"
            "  With conda: conda create -n ledger python=3.11 -y && conda activate ledger"
        )

    if not in_project_venv():
        if not VENV_PYTHON.exists():
            say("Creating virtual environment in .venv")
            subprocess.check_call([sys.executable, "-m", "venv", str(VENV)])
        result = subprocess.call([str(VENV_PYTHON), str(ROOT / "run.py"), *sys.argv[1:]])
        sys.exit(result)

    req_files = [ROOT / "requirements.txt"]
    if with_dev:
        req_files.append(ROOT / "requirements-dev.txt")

    digest = hashlib.sha256(b"".join(p.read_bytes() for p in req_files)).hexdigest()
    marker = VENV / (".installed-dev" if with_dev else ".installed")
    if marker.exists() and marker.read_text().strip() == digest:
        return

    say("Installing Python dependencies")
    cmd = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "-q"]
    for path in req_files:
        cmd += ["-r", str(path)]
    if subprocess.call(cmd) != 0:
        fail("pip install failed. Check your internet connection and try again.")
    marker.write_text(digest)


def _newest_mtime(paths) -> float:
    newest = 0.0
    for path in paths:
        if path.is_dir():
            for file in path.rglob("*"):
                if file.is_file():
                    newest = max(newest, file.stat().st_mtime)
        elif path.exists():
            newest = max(newest, path.stat().st_mtime)
    return newest


def frontend_is_stale() -> bool:
    index = DIST / "index.html"
    if not index.exists():
        return True
    sources = [
        FRONTEND / "src",
        FRONTEND / "public",
        FRONTEND / "index.html",
        FRONTEND / "package.json",
        FRONTEND / "vite.config.js",
    ]
    return _newest_mtime(sources) > index.stat().st_mtime


def npm_install_if_needed(npm: str) -> None:
    lock = FRONTEND / "node_modules" / ".package-lock.json"
    pkg = FRONTEND / "package.json"
    if lock.exists() and lock.stat().st_mtime >= pkg.stat().st_mtime:
        return
    say("Installing frontend dependencies (npm install)")
    if subprocess.call([npm, "install", "--no-audit", "--no-fund"], cwd=FRONTEND) != 0:
        fail("npm install failed.")


def ensure_frontend_build() -> None:
    if not frontend_is_stale():
        return

    npm = shutil.which("npm")
    has_build = (DIST / "index.html").exists()

    if npm is None:
        if has_build:
            say("Node.js not found. Using the existing frontend build in frontend/dist.")
            return
        fail(
            "The frontend has not been built and Node.js was not found.\n"
            "  Install Node.js 18+ from https://nodejs.org and run this again."
        )

    npm_install_if_needed(npm)
    say("Building the frontend")
    if subprocess.call([npm, "run", "build"], cwd=FRONTEND) != 0:
        if has_build:
            say("Build failed. Falling back to the previous build.")
            return
        fail("Frontend build failed.")


def port_is_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def pick_port(host: str, preferred: int) -> int:
    for port in range(preferred, preferred + 20):
        if port_is_free(host, port):
            if port != preferred:
                say(f"Port {preferred} is busy, using {port}")
            return port
    fail(f"No free port found between {preferred} and {preferred + 19}.")
    return preferred


def open_browser_when_ready(health_url: str, page_url: str, timeout: float = 30) -> None:
    def wait_and_open():
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(health_url, timeout=1):
                    webbrowser.open(page_url)
                    return
            except Exception:
                time.sleep(0.25)

    threading.Thread(target=wait_and_open, daemon=True).start()


def seed_demo_data() -> None:
    sys.path.insert(0, str(BACKEND))
    from decimal import Decimal

    from app import ledger
    from app.database import connect, init_db

    init_db(DB_FILE)
    conn = connect(DB_FILE)
    try:
        if conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]:
            say("Database already has accounts, skipping demo data")
            return

        demo = {
            "Meera Iyer": [
                ("credit", "85000", "Salary for September", "SAL-2609"),
                ("debit", "28000", "Rent for October", "RENT-2610"),
                ("debit", "3150.75", "Electricity and internet", "UTIL-2610"),
                ("credit", "12500", "Freelance design invoice #114", "INV-114"),
                ("debit", "6400", "Groceries", "CARD-88213"),
                ("debit", "15000", "Transfer to savings", "SAV-2610"),
                ("credit", "85000", "Salary for October", "SAL-2610"),
                ("debit", "28000", "Rent for November", "RENT-2611"),
                ("debit", "2199", "Annual software subscription", "SUB-7731"),
                ("debit", "1840.5", "Dinner with team", "CARD-88290"),
                ("credit", "4200", "Refund from airline", "RFND-5521"),
                ("debit", "9999", "New headphones", "CARD-88302"),
            ],
            "Northwind Supplies": [
                ("credit", "250000", "Opening capital", "CAP-001"),
                ("debit", "64000", "Inventory purchase, batch 12", "PO-1012"),
                ("credit", "38250", "Order #5531 settled", "ORD-5531"),
                ("debit", "12000", "Warehouse lease", "LEASE-11"),
            ],
            "Arjun Mehta": [],
        }
        for name, entries in demo.items():
            account = ledger.create_account(conn, name)
            for type_, amount, description, ref in entries:
                ledger.post_transaction(
                    conn, account["id"], type=type_, amount=Decimal(amount),
                    description=description, reference_id=ref,
                )
                time.sleep(0.002)
        say("Added demo accounts")
    finally:
        conn.close()


def run_server(host: str, port: int, open_browser: bool) -> None:
    sys.path.insert(0, str(BACKEND))
    import uvicorn

    from app.main import create_app

    app = create_app(db_path=DB_FILE, frontend_dist=DIST)
    url = f"http://{'localhost' if host in ('127.0.0.1', '0.0.0.0') else host}:{port}"

    print()
    say(f"Ledger is running at {url}")
    say(f"API docs at {url}/api/docs")
    say("Press Ctrl+C to stop\n")

    if open_browser:
        open_browser_when_ready(f"http://127.0.0.1:{port}/api/health", url)
    uvicorn.run(app, host=host, port=port, log_level="warning")


def run_dev(host: str, port: int, open_browser: bool) -> None:
    npm = shutil.which("npm")
    if npm is None:
        fail("Dev mode needs Node.js 18+ (https://nodejs.org).")
    npm_install_if_needed(npm)

    env = {**os.environ, "LEDGER_DB_PATH": str(DB_FILE), "LEDGER_FRONTEND_DIST": str(ROOT / ".no-dist")}
    api = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:create_app", "--factory", "--reload",
         "--host", host, "--port", str(port)],
        cwd=BACKEND, env=env,
    )
    web = subprocess.Popen(
        [npm, "run", "dev", "--", "--host", host],
        cwd=FRONTEND, env={**env, "LEDGER_API_URL": f"http://127.0.0.1:{port}"},
    )
    say(f"API on http://localhost:{port}, UI on http://localhost:5173")
    if open_browser:
        open_browser_when_ready(f"http://127.0.0.1:{port}/api/health", "http://localhost:5173")
    try:
        while api.poll() is None and web.poll() is None:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for proc in (web, api):
            if proc.poll() is None:
                proc.terminate()
        for proc in (web, api):
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Transaction Ledger.")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--no-browser", action="store_true", help="don't open a browser tab")
    parser.add_argument("--seed", action="store_true", help="add demo accounts if the database is empty")
    parser.add_argument("--dev", action="store_true", help="hot reload backend and frontend")
    parser.add_argument("--test", action="store_true", help="run the backend tests")
    parser.add_argument("--reset", action="store_true", help="delete the local database")
    args = parser.parse_args()

    if args.reset:
        removed = False
        for suffix in ("", "-wal", "-shm"):
            path = Path(f"{DB_FILE}{suffix}")
            if path.exists():
                path.unlink()
                removed = True
        say("Database deleted" if removed else "No database to delete")
        return

    ensure_python_env(with_dev=args.test)

    if args.test:
        sys.exit(subprocess.call([sys.executable, "-m", "pytest", "-q"], cwd=BACKEND))

    if args.seed:
        seed_demo_data()

    try:
        if args.dev:
            run_dev(args.host, pick_port(args.host, args.port), not args.no_browser)
        else:
            ensure_frontend_build()
            run_server(args.host, pick_port(args.host, args.port), not args.no_browser)
    except KeyboardInterrupt:
        print()
        say("Stopped")


if __name__ == "__main__":
    main()
