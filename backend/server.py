"""
Legacy server.py - Import from new main.py
This file is kept for backward compatibility with supervisor config
"""

# Import the new FastAPI app
from backend.main import app

# This makes 'app' available for: uvicorn server:app
# The app is now fully configured in backend/main.py