#!/usr/bin/env python3
"""
Default configuration for Autobot.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LLM configuration
LLM_CONFIG = {
    "model": os.getenv("LLM_MODEL", "gpt-4.1-mini"),
    "api_key": os.getenv("OPENAI_API_KEY"),
    "embedding_model": "text-embedding-3-small",
}

# Project configuration
PROJECT_CONFIG = {
    "projects_dir": "projects",
    "screenshots_dir": "screenshots",
}

# API configuration
API_CONFIG = {
    "host": "0.0.0.0",
    "port": int(os.getenv("API_PORT", "8000")),
    "debug": os.getenv("DEBUG", "False").lower() == "true",
}

# Tool configuration
TOOL_CONFIG = {
    "cli": {
        "enabled": True,
    },
    "python": {
        "enabled": True,
    },
    "computer_vision": {
        "enabled": True,
    },
    "file": {
        "enabled": True,
    },
    "web_search": {
        "enabled": True,
        "google_api_key": os.getenv("GOOGLE_API_KEY"),
        "google_cse_id": os.getenv("GOOGLE_CSE_ID"),
    },
}

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "standard",
            "filename": "autobot.log",
            "mode": "a",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True
        },
        "autobot": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False
        },
    },
}
