"""HTTP contract tests. The lifespan (model preload, queue workers) is not
started, so only routes that do not run inference are exercised here; the
full pipeline is covered by the end-to-end run described in CONTRIBUTING.md."""

import asyncio

import pytest
from fastapi.testclient import TestClient

from app.database import init_database
from app.main import app


@pytest.fixture(scope="module")
def client():
    asyncio.run(init_database())
    return TestClient(app)


def test_engines_endpoint_lists_all_engines(client):
    r = client.get("/api/engines")
    assert r.status_code == 200
    body = r.json()
    engines = body["engines"] if isinstance(body, dict) else body
    assert len(engines) == 23


@pytest.mark.parametrize("path", ["/api/analyze", "/api/quick-score"])
def test_rejects_short_text(client, path):
    r = client.post(path, json={"text": "too short"})
    assert r.status_code == 400
    assert "50 characters" in r.json()["error"]


@pytest.mark.parametrize("path", ["/api/analyze", "/api/quick-score"])
def test_rejects_empty_request(client, path):
    r = client.post(path, json={})
    assert r.status_code == 400


def test_home_page_renders(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "SlopTotal" in r.text


def test_form_rejects_short_text(client):
    r = client.post("/analyze", data={"text": "short"})
    assert r.status_code == 200
    assert "at least 50 characters" in r.text


def test_unknown_report_is_404(client):
    assert client.get("/report/abc123").status_code == 404


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["engines"] == 23
