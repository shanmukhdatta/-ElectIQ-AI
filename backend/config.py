"""ElectIQ application configuration."""
import os

class Config:
    """Central configuration loaded from environment variables."""
    GROQ_MODEL: str = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
    GEMINI_MODEL: str = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
    MAX_TOKENS: int = int(os.getenv('MAX_TOKENS', '1000'))
    TEMPERATURE: float = float(os.getenv('TEMPERATURE', '0.3'))
    DEFAULT_CONSTITUENCY: str = 'Mumbai North'
    RATE_LIMIT_CHAT: str = '20 per minute'
    RATE_LIMIT_VOTER: str = '10 per minute'
    CACHE_TIMEOUT_STATIC: int = 3600
    CACHE_TIMEOUT_CANDIDATES: int = 600
    MAX_CHAT_LEN: int = 2000
    MAX_EPIC_LEN: int = 10
