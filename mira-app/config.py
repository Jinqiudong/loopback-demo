"""
Loads environment variables once, at import time, so every other module
can just do `from config import SLACK_BOT_TOKEN` instead of re-reading
the .env file everywhere.
"""

import os
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Fail fast and loud if something required is missing, rather than
# getting a confusing error three layers deep at runtime.
_required = {
    "SLACK_BOT_TOKEN": SLACK_BOT_TOKEN,
    "SLACK_APP_TOKEN": SLACK_APP_TOKEN,
    "ANTHROPIC_API_KEY": ANTHROPIC_API_KEY,
}
_missing = [name for name, value in _required.items() if not value]
if _missing:
    raise RuntimeError(
        f"Missing required environment variable(s): {', '.join(_missing)}. "
        f"Copy .env.example to .env and fill in real values."
    )
