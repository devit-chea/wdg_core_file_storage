import httpx
import logging
import time
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ExternalAPIError(Exception):
    """Custom exception for external API errors."""
    pass


class ExternalAPIClient:
    """
    A reusable HTTP client for making external API requests with retry logic and error handling.

    :param base_url: The base URL for the API.
    :param headers: Default headers to include in every request.
    :param timeout: Default timeout for requests (in seconds).
    """
    def __init__(
        self,
        base_url: str = "",
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10,
    ):
        """
        Initialize the ExternalAPIClient.

        :param base_url: The base URL for the API.
        :param headers: Default headers to include in every request.
        :param timeout: Default timeout for requests (in seconds).
        """
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self.timeout = timeout

    def _get_full_url(self, endpoint: str) -> str:
        """
        Construct the full URL for a given endpoint.

        :param endpoint: The API endpoint path.
        :return: The full URL as a string.
        """
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Any = None,
        json: Any = None,
        headers: Optional[Dict] = None,
        timeout: Optional[int] = None,
        retries: int = 3,
        retry_delay: float = 1.0,
    ) -> httpx.Response:
        """
        Make an HTTP request with optional retries and error handling.
        Raises ExternalAPIError on failure.

        :param method: HTTP method (GET, POST, etc.).
        :param endpoint: API endpoint path.
        :param params: Query parameters.
        :param data: Form data.
        :param json: JSON body.
        :param headers: Additional headers.
        :param timeout: Request timeout (seconds).
        :param retries: Number of retry attempts for transient errors.
        :param retry_delay: Delay between retries (seconds).
        :return: httpx.Response object.
        :raises ExternalAPIError: On request failure.
        """
        url = self._get_full_url(endpoint)
        all_headers = {**self.headers, **(headers or {})}
        last_exception = None
        for attempt in range(1, retries + 1):
            try:
                with httpx.Client(timeout=timeout or self.timeout) as client:
                    response = client.request(
                        method=method.upper(),
                        url=url,
                        params=params,
                        data=data,
                        json=json,
                        headers=all_headers,
                    )
                    response.raise_for_status()
                    return response
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
                last_exception = e
                if 500 <= e.response.status_code < 600 and attempt < retries:
                    time.sleep(retry_delay)
                    continue
                raise ExternalAPIError(f"HTTP error: {e.response.status_code} - {e.response.text}") from e
            except httpx.RequestError as e:
                logger.error(f"Request failed: {str(e)}")
                last_exception = e
                if attempt < retries:
                    time.sleep(retry_delay)
                    continue
                raise ExternalAPIError(f"Request failed: {str(e)}") from e
        raise ExternalAPIError(f"Request failed after {retries} attempts: {last_exception}")

    def get(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        retries: int = 3,
        retry_delay: float = 1.0,
    ) -> httpx.Response:
        """
        Send a GET request.

        :param endpoint: API endpoint path.
        :param params: Query parameters.
        :param headers: Additional headers.
        :param retries: Number of retry attempts.
        :param retry_delay: Delay between retries (seconds).
        :return: httpx.Response object.
        """
        return self.request("GET", endpoint, params=params, headers=headers, retries=retries, retry_delay=retry_delay)

    def post(
        self,
        endpoint: str,
        json: Any = None,
        data: Any = None,
        headers: Optional[Dict] = None,
        retries: int = 3,
        retry_delay: float = 1.0,
    ) -> httpx.Response:
        """
        Send a POST request.

        :param endpoint: API endpoint path.
        :param json: JSON body.
        :param data: Form data.
        :param headers: Additional headers.
        :param retries: Number of retry attempts.
        :param retry_delay: Delay between retries (seconds).
        :return: httpx.Response object.
        """
        return self.request("POST", endpoint, json=json, data=data, headers=headers, retries=retries, retry_delay=retry_delay)

    def put(
        self,
        endpoint: str,
        json: Any = None,
        headers: Optional[Dict] = None,
        retries: int = 3,
        retry_delay: float = 1.0,
    ) -> httpx.Response:
        """
        Send a PUT request.

        :param endpoint: API endpoint path.
        :param json: JSON body.
        :param headers: Additional headers.
        :param retries: Number of retry attempts.
        :param retry_delay: Delay between retries (seconds).
        :return: httpx.Response object.
        """
        return self.request("PUT", endpoint, json=json, headers=headers, retries=retries, retry_delay=retry_delay)

    def delete(
        self,
        endpoint: str,
        headers: Optional[Dict] = None,
        retries: int = 3,
        retry_delay: float = 1.0,
    ) -> httpx.Response:
        """
        Send a DELETE request.

        :param endpoint: API endpoint path.
        :param headers: Additional headers.
        :param retries: Number of retry attempts.
        :param retry_delay: Delay between retries (seconds).
        :return: httpx.Response object.
        """
        return self.request("DELETE", endpoint, headers=headers, retries=retries, retry_delay=retry_delay)
