"""Configuration settings for Andy AI Bot."""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Centralized configuration management for the bot."""

    # Discord Settings
    DISCORD_TOKEN: str = os.getenv("DISCORD_API_TOKEN", "")
    COMMAND_PREFIX: str = "$"
    CASE_INSENSITIVE: bool = True

    # OpenAI Settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_MAX_RETRIES: int = 3
    LLM_TIMEOUT_SECONDS: int = 30
    LLM_REQUEST_TIMEOUT_SECONDS: float = 30.0

    # Discord Message Settings
    MAX_MESSAGE_LENGTH: int = 1900  # Discord limit is 2000, leave buffer
    TYPING_INDICATOR_ENABLED: bool = True

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_CALLS_PER_USER_PER_MINUTE: int = 5
    RATE_LIMIT_CALLS_PER_GUILD_PER_MINUTE: int = 20

    # System Prompt
    SYSTEM_PROMPT: str = (
        "You are Andy, a robotic helper with the goal of providing one-to-two sentence responses to questions. "
        "If you are asked something that you cannot answer within a reasonable conciseness, ask the user to ask a different question. "
        "You can make jokes, or make fun of users' queries."
    )

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE", "bot.log")

    # Feature Flags
    CACHING_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 3600  # 1 hour

    @classmethod
    def validate(cls) -> None:
        """Validate critical configuration values."""
        if not cls.DISCORD_TOKEN:
            raise ValueError("DISCORD_API_TOKEN environment variable is required")
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")

    @classmethod
    def to_dict(cls) -> dict:
        """Export non-sensitive config as dictionary."""
        return {
            "command_prefix": cls.COMMAND_PREFIX,
            "llm_model": cls.LLM_MODEL,
            "max_message_length": cls.MAX_MESSAGE_LENGTH,
            "caching_enabled": cls.CACHING_ENABLED,
            "rate_limiting_enabled": cls.RATE_LIMIT_ENABLED,
        }
