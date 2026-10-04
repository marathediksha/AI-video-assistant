import time
from typing import Any


def invoke_with_retry(chain: Any, value: Any, attempts: int = 3) -> Any:
    """Invoke an LLM chain and retry temporary provider errors."""
    for attempt in range(attempts):
        try:
            return chain.invoke(value)
        except Exception as error:
            message = str(error).lower()
            is_rate_limited = (
                "429" in message
                or "rate limit" in message
                or "rate_limited" in message
            )
            is_temporarily_unavailable = (
                "503" in message
                or "unavailable" in message
                or "high demand" in message
            )
            is_retryable = is_rate_limited or is_temporarily_unavailable
            if not is_retryable or attempt == attempts - 1:
                if is_rate_limited:
                    raise RuntimeError(
                        "The AI provider rate limit was reached. Wait a few minutes "
                        "and try again."
                    ) from error
                if is_temporarily_unavailable:
                    raise RuntimeError(
                        "The AI provider is temporarily unavailable due to high demand. "
                        "Please wait a few minutes and try again."
                    ) from error
                raise
            time.sleep(10 * (2 ** attempt))
