"""
Configuration and environment variables for the Pitch Deck Agent.
"""
import os
from pathlib import Path

# ── API Keys ──────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON", "")  # Service account JSON

# ── Model Config ──────────────────────────────────────────────────────
GEMINI_MODEL = "gemini-2.0-flash"
CLAUDE_MODEL = "claude-sonnet-4-5-20250514"
SYNTHESIS_PROVIDER = os.getenv("SYNTHESIS_PROVIDER", "gemini")  # "gemini" or "claude"

# ── Processing Limits ─────────────────────────────────────────────────
MAX_UPLOAD_FILES = 10
MAX_FILE_SIZE_MB = 50
MAX_PDF_PAGES = 100
SUPPORTED_EXTENSIONS = {
    "documents": [".pdf", ".txt", ".md", ".rtf"],
    "emails": [".eml", ".msg"],
    "images": [".png", ".jpg", ".jpeg", ".webp", ".gif"],
    "video": [".mp4", ".mov", ".avi", ".mkv"],
}

# ── Paths ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
TEMP_DIR = BASE_DIR / "tmp"
TEMP_DIR.mkdir(exist_ok=True)

# ── Deck Defaults ─────────────────────────────────────────────────────
DEFAULT_SLIDE_COUNT = 10
DEFAULT_DECK_TITLE = "Untitled Pitch Deck"

# ── Google Slides ─────────────────────────────────────────────────────
GOOGLE_SLIDES_SCOPES = [
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/drive.file",
]
