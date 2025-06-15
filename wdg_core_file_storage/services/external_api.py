import httpx
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ExternalAPIClient:
    def __init__(
        self,
        base_url: str = "",
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10,
    ):
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self.timeout = timeout

    def _get_full_url(self, endpoint: str) -> str:
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
    ) -> httpx.Response:
        url = self._get_full_url(endpoint)
        all_headers = {**self.headers, **(headers or {})}
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
            raise
        except httpx.RequestError as e:
            logger.error(f"Request failed: {str(e)}")
            raise

    def get(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ):
        return self.request("GET", endpoint, params=params, headers=headers)

    def post(
        self,
        endpoint: str,
        json: Any = None,
        data: Any = None,
        headers: Optional[Dict] = None,
    ):
        return self.request("POST", endpoint, json=json, data=data, headers=headers)

    def put(self, endpoint: str, json: Any = None, headers: Optional[Dict] = None):
        return self.request("PUT", endpoint, json=json, headers=headers)

    def delete(self, endpoint: str, headers: Optional[Dict] = None):
        return self.request("DELETE", endpoint, headers=headers)
