import time
import random
from typing import Optional, Callable, Any, Dict
import httpx

from backend.integrations.servicenow.exceptions import (
    ServiceNowRateLimitError,
    ServiceNowTransientError,
    ServiceNowPermanentError,
    ServiceNowAuthError,
    ServiceNowNotFoundError
)

class RateLimiter:
    """Token-bucket rate limiter ensuring outbound requests respect RPS limit."""
    def __init__(self, requests_per_second: float = 10.0):
        self.rps = max(1.0, requests_per_second)
        self.min_interval = 1.0 / self.rps
        self._last_request_time: float = 0.0

    def acquire(self):
        """Blocks briefly if needed to enforce minimum request interval."""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_request_time = time.time()


def parse_retry_after(response: httpx.Response, default: float = 5.0) -> float:
    """Parses Retry-After header (seconds or HTTP date) with safety fallback."""
    raw = response.headers.get("Retry-After")
    if not raw:
        return default
    try:
        val = float(raw)
        return max(1.0, min(val, 60.0))  # Bound between 1s and 60s
    except ValueError:
        return default


def execute_with_retry(
    operation: Callable[[], httpx.Response],
    max_retries: int = 3,
    backoff_base: float = 1.5,
    on_rate_limit: Optional[Callable[[float], None]] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None
) -> httpx.Response:
    """
    Executes an HTTP operation with rate-limit handling and exponential backoff retry.
    Classifies HTTP status codes into domain exceptions.
    """
    attempt = 0
    while True:
        try:
            resp = operation()
            status = resp.status_code

            # Success
            if 200 <= status < 300:
                return resp

            # 401 / 403 Authentication / Authorization
            if status in (401, 403):
                raise ServiceNowAuthError(
                    f"ServiceNow authentication/authorization error (HTTP {status}): {resp.text}",
                    details={"status_code": status, "body": resp.text[:500]}
                )

            # 404 Not Found
            if status == 404:
                raise ServiceNowNotFoundError(
                    f"ServiceNow resource not found (HTTP 404): {resp.text}",
                    details={"status_code": 404, "body": resp.text[:500]}
                )

            # 429 Rate Limited
            if status == 429:
                retry_after = parse_retry_after(resp)
                if on_rate_limit:
                    on_rate_limit(retry_after)
                if attempt < max_retries:
                    attempt += 1
                    sleep_time = retry_after + random.uniform(0.1, 0.5)
                    if on_retry:
                        on_retry(attempt, ServiceNowRateLimitError("Rate limit exceeded", retry_after=retry_after))
                    time.sleep(sleep_time)
                    continue
                else:
                    raise ServiceNowRateLimitError(
                        f"ServiceNow rate limit exceeded after {max_retries} retries.",
                        retry_after=retry_after,
                        details={"status_code": 429}
                    )

            # 5xx Transient Server Errors & 408 Request Timeout
            if status in (408, 500, 502, 503, 504):
                if attempt < max_retries:
                    attempt += 1
                    sleep_time = (backoff_base ** attempt) + random.uniform(0.1, 0.5)
                    err = ServiceNowTransientError(f"HTTP {status} transient error", status_code=status)
                    if on_retry:
                        on_retry(attempt, err)
                    time.sleep(sleep_time)
                    continue
                else:
                    raise ServiceNowTransientError(
                        f"ServiceNow transient server error HTTP {status} persisted after {max_retries} attempts: {resp.text}",
                        status_code=status,
                        details={"status_code": status, "body": resp.text[:500]}
                    )

            # Other 4xx Client Permanent Errors
            raise ServiceNowPermanentError(
                f"ServiceNow client error HTTP {status}: {resp.text}",
                status_code=status,
                details={"status_code": status, "body": resp.text[:500]}
            )

        except httpx.RequestError as exc:
            # Network/timeout exceptions are transient
            if attempt < max_retries:
                attempt += 1
                sleep_time = (backoff_base ** attempt) + random.uniform(0.1, 0.5)
                err = ServiceNowTransientError(f"Network error: {str(exc)}")
                if on_retry:
                    on_retry(attempt, err)
                time.sleep(sleep_time)
                continue
            else:
                raise ServiceNowTransientError(
                    f"ServiceNow request failed after {max_retries} network attempts: {str(exc)}"
                ) from exc
