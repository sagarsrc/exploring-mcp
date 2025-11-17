"""
Base HTTP client with common functionality.

Provides shared HTTP client capabilities including:
- Connection pooling
- Automatic retries with exponential backoff
- Timeout handling
- Common headers management
"""

from typing import Dict, Optional, Any
import httpx
from abc import ABC, abstractmethod


class BaseHTTPClient(ABC):
    """
    Abstract base class for HTTP API clients.

    Provides common HTTP client functionality with retries, timeouts,
    and connection pooling.
    """

    def __init__(
        self,
        base_url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """
        Initialize base HTTP client.

        Args:
            base_url: Base URL for API endpoints
            headers: Default headers to include in all requests
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        # Create HTTP client with connection pooling
        self.client = httpx.Client(
            base_url=self.base_url,
            headers=headers or {},
            timeout=timeout,
            transport=httpx.HTTPTransport(retries=max_retries),
        )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.close()

    def close(self):
        """Close the HTTP client and release connections."""
        self.client.close()

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """
        Make HTTP request with error handling.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (relative to base_url)
            params: Query parameters
            json: JSON request body
            headers: Additional headers for this request

        Returns:
            HTTP response object

        Raises:
            httpx.HTTPError: For HTTP errors
            httpx.TimeoutException: For timeout errors
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        response = self.client.request(
            method=method,
            url=url,
            params=params,
            json=json,
            headers=headers,
        )

        response.raise_for_status()
        return response

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Make GET request."""
        return self._request("GET", endpoint, params=params, headers=headers)

    def post(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Make POST request."""
        return self._request("POST", endpoint, json=json, headers=headers)

    def put(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Make PUT request."""
        return self._request("PUT", endpoint, json=json, headers=headers)

    def patch(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Make PATCH request."""
        return self._request("PATCH", endpoint, json=json, headers=headers)

    def delete(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Make DELETE request."""
        return self._request("DELETE", endpoint, headers=headers)

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the API is accessible.

        Returns:
            True if API is healthy, False otherwise
        """
        pass
