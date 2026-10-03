import httpx
from ._client import BASE_URL

def _request_handler(method: str, endpoint: str, timeout: int = 30, **kwargs):
    with httpx.Client(base_url=BASE_URL, timeout=timeout) as http:
        resp = http.request(method, endpoint, **kwargs)
        resp.raise_for_status()
        return resp.json()

def register(email: str, password: str):
    return _request_handler("POST", "/auth", json={"email" : email, "password" : password})

def request_reset_password(email: str):
    return _request_handler("POST", "/forgot-password", json={"email" : email})

def reset_password(token: str, new_password: str):
    return _request_handler("PUT", "/reset-password", json={"token" : token, "new_password" : new_password})
