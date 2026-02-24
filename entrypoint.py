#!/usr/bin/env python3
"""
Application entrypoint for Clever Photos API.

This module:
1. Loads environment variables first
2. Configures logging before any other imports
3. Imports and runs the FastAPI application
"""

from dotenv import load_dotenv

# Load environment variables FIRST, before any other imports
load_dotenv()

# Configure logging BEFORE importing the app
from clever.config import Settings
from clever.logging import configure_logging

# Load settings and configure logging
settings = Settings()
configure_logging(settings)

# Now import the FastAPI app
from clever.main import app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "clever.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.is_development,
        log_config=None,  # We handle logging ourselves
    )
