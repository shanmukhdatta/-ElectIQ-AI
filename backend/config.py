"""
ElectIQ — Centralised Application Configuration
All environment variables and constants live here.
"""
import os


class Config:
    """Production configuration loaded from environment variables."""

    # ── LLM Providers ─────────────────────────────────────────────────────
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "1000"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.3"))

    # ── Google Cloud ───────────────────────────────────────────────────────
    GOOGLE_CLOUD_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT", "electiq-demo")
    GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
    FIREBASE_CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "")
    BIGQUERY_DATASET: str = os.getenv("BIGQUERY_DATASET", "electiq_analytics")

    # ── Rate Limits ────────────────────────────────────────────────────────
    RATE_LIMIT_CHAT: str = "20 per minute"
    RATE_LIMIT_VOTER: str = "10 per minute"
    RATE_LIMIT_AI: str = "10 per minute"
    RATE_LIMIT_DEFAULT: str = "200 per day, 50 per hour"

    # ── Caching ────────────────────────────────────────────────────────────
    CACHE_TIMEOUT_STATIC: int = 3600     # 1 hour for quiz/timeline
    CACHE_TIMEOUT_CANDIDATES: int = 600  # 10 min for candidates
    CACHE_TIMEOUT_DEFAULT: int = 300     # 5 min default

    # ── Validation ─────────────────────────────────────────────────────────
    MAX_CHAT_MESSAGE_LEN: int = 2000
    MAX_EPIC_LEN: int = 10
    MAX_CLAIM_LEN: int = 500
    MAX_REQUEST_SIZE: int = 16 * 1024   # 16KB

    # ── App ────────────────────────────────────────────────────────────────
    DEFAULT_CONSTITUENCY: str = "Mumbai North"
    VOTER_HELPLINE: str = "1950"
    ECI_PORTAL: str = "https://electoralsearch.in"
    NVSP_PORTAL: str = "https://nvsp.in"
