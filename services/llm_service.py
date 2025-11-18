"""LLM Service with error handling, retries, and caching."""
import time
from typing import Optional, List, Dict, Any
from openai import OpenAI, APIError, APIConnectionError, APITimeoutError
from config import Config
from utils.logger import get_logger
from utils.cache import SimpleCache


logger = get_logger(__name__)


class LLMService:
    """Service for interacting with OpenAI API with error handling and caching."""

    def __init__(self, api_key: str = None):
        """
        Initialize LLM Service.
        
        Args:
            api_key: OpenAI API key (defaults to config value)
        """
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key)
        self.model = Config.LLM_MODEL
        self.max_retries = Config.LLM_MAX_RETRIES
        self.timeout = Config.LLM_REQUEST_TIMEOUT_SECONDS
        
        # Initialize cache
        self.cache: Optional[SimpleCache[str]] = None
        if Config.CACHING_ENABLED:
            self.cache = SimpleCache(ttl_seconds=Config.CACHE_TTL_SECONDS)
        
        logger.info(f"LLMService initialized with model: {self.model}")

    def _build_cache_key(self, system_prompt: str, user_prompt: str) -> str:
        """
        Build cache key from prompts.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
        
        Returns:
            Cache key string
        """
        return f"{hash(system_prompt)}:{hash(user_prompt)}"

    def ask(self, prompt: str, system_prompt: str = None) -> str:
        """
        Ask LLM a question with automatic retries and error handling.
        
        Args:
            prompt: User prompt/question
            system_prompt: System prompt (defaults to config value)
        
        Returns:
            LLM response text
        
        Raises:
            ValueError: If prompts are empty
            RuntimeError: If all retries fail
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        system_prompt = system_prompt or Config.SYSTEM_PROMPT

        # Check cache first
        if self.cache:
            cache_key = self._build_cache_key(system_prompt, prompt)
            cached_response = self.cache.get(cache_key)
            if cached_response:
                logger.debug(f"Cache hit for prompt: {prompt[:50]}...")
                return cached_response

        # Attempt request with retries
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    timeout=self.timeout,
                )

                output = response.choices[0].message.content.strip()

                # Cache successful response
                if self.cache:
                    cache_key = self._build_cache_key(system_prompt, prompt)
                    self.cache.set(cache_key, output)

                logger.info(f"Successfully got LLM response for prompt: {prompt[:50]}...")
                return output

            except APITimeoutError as e:
                last_error = e
                logger.warning(
                    f"Timeout on attempt {attempt}/{self.max_retries}: {str(e)}"
                )
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)

            except APIConnectionError as e:
                last_error = e
                logger.warning(
                    f"Connection error on attempt {attempt}/{self.max_retries}: {str(e)}"
                )
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)

            except APIError as e:
                last_error = e
                logger.error(f"API error on attempt {attempt}/{self.max_retries}: {str(e)}")
                
                # Don't retry on authentication/rate limit errors immediately
                if "401" in str(e) or "403" in str(e):
                    raise RuntimeError(f"Authentication error: {str(e)}")
                
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error on attempt {attempt}/{self.max_retries}: {str(e)}")
                if attempt < self.max_retries:
                    time.sleep(1)

        # All retries exhausted
        error_msg = f"Failed to get LLM response after {self.max_retries} attempts: {str(last_error)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    def clear_cache(self) -> None:
        """Clear response cache."""
        if self.cache:
            self.cache.clear()
            logger.info("LLM response cache cleared")
