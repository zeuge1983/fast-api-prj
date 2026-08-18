"""Shared fixtures.

This file also has to exist at the repo root so pytest puts the root on
sys.path, which is what makes `from app.main import app` resolve in tests.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

# The demo agent token from app/auth.py. Every case needs auth except the
# two that deliberately test its absence.
AUTH = {"Authorization": "Bearer valid-token"}

CASSETTE_DIR = Path(__file__).parent / "tests" / "cassettes"


@pytest.fixture(scope="session")
def client():
    """The app itself, called in-process — no uvicorn, no port, no network.

    TestClient wraps the ASGI `app` object and invokes it directly, so a
    `client.get(...)` is a Python function call, not an HTTP request.
    """
    with TestClient(app) as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# A stand-in for the model client. It mimics only the sliver of the OpenAI SDK
# that app.ai touches: client.chat.completions.create(...) -> response with
# .choices[0].message.content
# ---------------------------------------------------------------------------

class FakeMessage:
    def __init__(self, content):
        self.content = content


class FakeChoice:
    def __init__(self, content):
        self.message = FakeMessage(content)


class FakeResponse:
    def __init__(self, choices):
        self.choices = choices


class FakeCompletions:
    def __init__(self, content=None, choices=None, error=None):
        self._content = content
        self._choices = choices
        self._error = error
        self.calls = []          # records every create() call for assertions

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self._error is not None:
            raise self._error
        if self._choices is not None:
            return FakeResponse(self._choices)
        return FakeResponse([FakeChoice(self._content)])


class FakeClient:
    """Quacks like openai.OpenAI for the one call path we use."""

    def __init__(self, content=None, choices=None, error=None):
        self.completions = FakeCompletions(content, choices, error)
        self.chat = type("Chat", (), {"completions": self.completions})()

    @property
    def calls(self):
        return self.completions.calls


def fake_model(content=None, **kwargs):
    """Build a stand-in model client that always replies with `content`."""
    return FakeClient(content=content, **kwargs)


# ---------------------------------------------------------------------------
# Cassettes: real replies from the local model, recorded to disk so tests can
# replay authentic output offline and instantly.
# ---------------------------------------------------------------------------

def load_cassette(name):
    """Return the raw reply text the real model gave for scenario `name`."""
    data = json.loads((CASSETTE_DIR / f"{name}.json").read_text())
    return data["reply"]


@pytest.fixture
def cassette():
    """Give a test a model client that replays a recorded real reply."""
    def _cassette(name):
        return fake_model(load_cassette(name))
    return _cassette
