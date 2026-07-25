from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import aiohttp

from .errors import ClovordHTTPError, ClovordInvalidTokenError


class HTTPClient:
    """Minimal async REST client for Clovord API."""

    BASE_URL = "https://clovord.com/api/v1"
    MAX_RETRY_AFTER_SECONDS = 30.0
    DEFAULT_RETRY_AFTER_SECONDS = 1.0

    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None
        self._token: str | None = None

    async def start(self, token: str) -> None:
        token_changed = self._token is not None and self._token != token
        self._token = token

        if self._session is not None and not self._session.closed and token_changed:
            await self._session.close()
            self._session = None

        if self._session is None or self._session.closed:
            headers = {
                "Authorization": f"Bot {token}",
                "Content-Type": "application/json",
            }
            self._session = aiohttp.ClientSession(headers=headers)

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()
        self._token = None

    async def get(self, path: str, **kwargs: Any) -> dict[str, Any]:
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> dict[str, Any]:
        return await self._request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs: Any) -> dict[str, Any]:
        return await self._request("PUT", path, **kwargs)

    async def patch(self, path: str, **kwargs: Any) -> dict[str, Any]:
        return await self._request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> dict[str, Any]:
        return await self._request("DELETE", path, **kwargs)

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        if self._session is None or self._session.closed:
            raise ClovordHTTPError("HTTP client is not started")

        normalized_path = path if path.startswith("/") else f"/{path}"
        url = f"{self.BASE_URL}{normalized_path}"

        try:
            for attempt in range(2):
                async with self._session.request(method, url, **kwargs) as response:
                    if response.status == 429 and attempt == 0:
                        await response.text()
                        retry_after = self._get_retry_after_seconds(response)
                        await asyncio.sleep(retry_after)
                        continue

                    if response.status in {401, 403}:
                        text = await response.text()
                        raise ClovordInvalidTokenError(f"Authentication failed: {text or response.reason}")

                    if response.status >= 400:
                        text = await response.text()
                        raise ClovordHTTPError(f"{response.status} {response.reason}: {text}")

                    if response.status == 204:
                        return {}

                    if response.content_type == "application/json":
                        return await response.json()

                    text = await response.text()
                    return {"raw": text} if text else {}

            raise ClovordHTTPError("429 Too Many Requests: retry limit reached")
        except aiohttp.ClientError as exc:
            raise ClovordHTTPError(str(exc)) from exc

    def _get_retry_after_seconds(self, response: aiohttp.ClientResponse) -> float:
        header_value = (response.headers.get("Retry-After") or "").strip()
        if not header_value:
            return self.DEFAULT_RETRY_AFTER_SECONDS

        try:
            retry_seconds = float(header_value)
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(header_value)
            except (TypeError, ValueError):
                return self.DEFAULT_RETRY_AFTER_SECONDS

            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            retry_seconds = (retry_at - now).total_seconds()

        bounded_retry = max(0.0, min(retry_seconds, self.MAX_RETRY_AFTER_SECONDS))
        return bounded_retry
