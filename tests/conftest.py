import httpx
import pytest

from flexreportfinance import FlexreportClient


@pytest.fixture
def api():
    """A client wired to a fake server; `api.requests` records every data call."""
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/token":
            return httpx.Response(200, json={"access_token": "tok"})
        if request.url.path == "/task-status":
            return httpx.Response(200, json={"status": "SUCCESS", "result": {"topics": ["ai"]}})
        requests.append(request)
        if request.url.path == "/get-earnings-topics":
            return httpx.Response(200, json={"task_id": "t-1", "status": "PENDING"})
        return httpx.Response(200, json={"ok": True})

    client = FlexreportClient("user", "pass")
    client._http = httpx.Client(base_url="https://api.test", transport=httpx.MockTransport(handler), auth=client._http.auth)
    client.requests = requests
    yield client
    client.close()
