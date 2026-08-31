"""
Vercel Serverless Function entrypoint for SANDHI FastAPI backend.
Exposes the FastAPI app from backend/app/main.py.
"""

import sys
from pathlib import Path

# Add backend directory to Python sys.path so app package imports work seamlessly
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app  # noqa: E402
