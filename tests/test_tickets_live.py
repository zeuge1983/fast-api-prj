"""One happy-path test over real HTTP against a running uvicorn.

TestClient calls the ASGI app directly, so it can never catch a problem that
lives in the server layer — a proxy, a header rewrite, a TLS or CORS setting.
This is the smallest test that does, which is why it is worth its slowness.

Run it deliberately:
    uvicorn app.main:app --port 8000     # in another terminal
    pytest -m live
"""

import pytest
import requests

pytestmark = pytest.mark.live

BASE_URL = "http://127.0.0.1:8000"
AUTH = {"Authorization": "Bearer valid-token"}


def test_ticket_retrieval_over_real_http():
    try:
        response = requests.get(f"{BASE_URL}/tickets/123", headers=AUTH, timeout=5)
    except requests.ConnectionError:
        # Fail loudly rather than skip: a silent skip looks like a pass.
        pytest.fail(
            f"No server at {BASE_URL}. Start it with:\n"
            f"    uvicorn app.main:app --port 8000"
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")

    body = response.json()
    assert body["id"] == 123
    assert body["customer"]["email"] == "bob@example.com"
