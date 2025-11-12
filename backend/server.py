"""
Legacy server.py - Import from new main.py
This file is kept for backward compatibility with supervisor config
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the new FastAPI app
from backend.main import app

# This makes 'app' available for: uvicorn server:app
# The app is now fully configured in backend/main.py