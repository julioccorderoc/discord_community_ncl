from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL: str = os.environ["SUPABASE_URL"]
SUPABASE_SECRET_KEY: str = os.environ["SUPABASE_SECRET_KEY"]
DISCORD_BOT_TOKEN: str = os.environ["DISCORD_BOT_TOKEN"]

# EPIC-003: Ticket System
STAFF_ROLE_ID: int | None = int(os.environ["STAFF_ROLE_ID"]) if os.environ.get("STAFF_ROLE_ID") else None
TICKET_CATEGORY_ID: int | None = int(os.environ["TICKET_CATEGORY_ID"]) if os.environ.get("TICKET_CATEGORY_ID") else None

# EPIC-005: AI Compliance Agent
GEMINI_API_KEY: str = os.environ["GEMINI_API_KEY"]
GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-lite")
GEMINI_TIMEOUT_SECONDS: int = int(os.environ.get("GEMINI_TIMEOUT_SECONDS", "20"))

# EPIC-006: Admin Dashboard
ADMIN_PASSWORD: str | None = os.environ.get("ADMIN_PASSWORD")
