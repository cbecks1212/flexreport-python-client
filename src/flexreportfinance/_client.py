from typing import Any

import httpx

from .catalog import Catalog
from .events import Events
from .reports import Reports

BASE_URL = "https://flexreportfinapi.com"


class _TokenAuth(httpx.Auth):
    """Adds the bearer token, fetching it on first use and again if the API answers 401."""

    def __init__(self, client: "FlexreportClient"):
        self._client = client
        self._token: str | None = None

    def auth_flow(self, request):
        if self._token is None:
            self._token = self._client._fetch_token()
        request.headers["Authorization"] = f"Bearer {self._token}"
        response = yield request

        if response.status_code == 401:
            self._token = self._client._fetch_token()
            request.headers["Authorization"] = f"Bearer {self._token}"
            yield request


class FlexreportClient:
    def __init__(self, username: str, password: str, base_url: str = BASE_URL, timeout: float = 30):
        self._username = username
        self._password = password
        self._http = httpx.Client(base_url=base_url, timeout=timeout, auth=_TokenAuth(self))

        self.catalog = Catalog(self)
        self.reports = Reports(self)
        self.events = Events(self)

    def _fetch_token(self) -> str:
        resp = self._http.post("/token", data={"username": self._username, "password": self._password}, auth=None)
        resp.raise_for_status()
        return resp.json()["access_token"]

    def _json(self, method: str, url: str, **kwargs) -> Any:
        resp = self._http.request(method, url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "FlexreportClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
