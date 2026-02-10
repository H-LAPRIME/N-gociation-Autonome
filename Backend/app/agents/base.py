import os
import logging
from typing import List, Optional
from agno.agent import Agent
from agno.models.mistral import MistralChat
from app.utils.api_retry import retry_with_exponential_backoff, mistral_rate_limiter

logger = logging.getLogger(__name__)


class BaseOmegaAgent:
    def __init__(
        self,
        name: str,
        instructions: List[str],
        tools: Optional[List] = None,
        temperature: float = 0.2,
        max_tokens: int = 512
    ):
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
        if not mistral_api_key:
            raise ValueError("MISTRAL_API_KEY non défini.")

        mistral_model = MistralChat(
            id="mistral-large-latest",
            api_key=mistral_api_key,
            temperature=temperature,
            max_tokens=max_tokens
        )

        self.agent = Agent(
            name=name,
            model=mistral_model,
            instructions=instructions,
            tools=tools,
            markdown=False
        )

    def run(self, message: str):
        return self.agent.run(message)

    async def arun(self, message: str):
        """
        Run agent with automatic retry on rate limit errors.
        """
        # Acquire rate limit token before making API call
        await mistral_rate_limiter.acquire()
        
        # Define the actual API call
        async def _make_api_call():
            try:
                response = await self.agent.arun(message)
                
                # Check response content for error messages that weren't raised as exceptions
                # Sometimes the API returns the error as a string in the content instead of raising
                content = getattr(response, "content", "") or getattr(response, "output_text", "") or str(response)
                
                if isinstance(content, str):
                    content_lower = content.lower()
                    # Check for rate limit indicators in the response text
                    if ("rate limit" in content_lower or "429" in content_lower or "rate_limited" in content_lower) and "error" in content_lower:
                        logger.warning(f"⚠️ Rate limit detected in response content for agent {self.agent.name}")
                        raise Exception(f"Rate limit exceeded: {content}")
                
                return response
            except Exception as e:
                error_msg = str(e).lower()
                # Check if it's a rate limit error
                if "rate limit" in error_msg or "429" in error_msg or "rate_limited" in error_msg:
                    logger.warning(f"⚠️ Rate limit hit for agent {self.agent.name}")
                    raise  # Will be caught by retry logic
                else:
                    # For other errors, log and re-raise
                    logger.error(f"❌ API error in {self.agent.name}: {e}")
                    raise
        
        # Retry callback to log retry attempts
        async def _on_retry(attempt: int, error: Exception, delay: float):
            logger.info(f"🔄 Retry {attempt + 1} for {self.agent.name} after {delay:.2f}s")
        
        # Use retry logic with exponential backoff
        return await retry_with_exponential_backoff(
            _make_api_call,
            max_retries=5,      # Increased from 3 to 5 for better rate limit handling
            initial_delay=3.0,  # Increased from 2.0 to 3.0 seconds
            max_delay=60.0,     # Max 60 seconds between retries
            exponential_base=2.0,
            jitter=True,
            on_retry=_on_retry
        )
