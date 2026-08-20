"""
WSGI config for config project.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from django.core.wsgi import get_wsgi_application


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(
    BASE_DIR / ".env"
)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings.development",
)

application = get_wsgi_application()