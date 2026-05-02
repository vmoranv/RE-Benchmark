"""End-to-end smoke for the API skeleton."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from apps.api.main import create_app


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app())


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_dimensions_listing(client):
    resp = client.get("/api/v1/dimensions/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 18
    assert body["items"][0]["code"] == "D01"


def test_submit_and_fetch_run(client):
    spec = {
        "sample_variant_id": "00000000-0000-0000-0000-000000000001",
        "dimension_code": "D01",
        "model_id": "anthropic/claude-opus-4-7",
        "seed": 1234,
    }
    submit = client.post("/api/v1/runs/", json=spec)
    assert submit.status_code == 201
    run = submit.json()
    assert run["state"] == "PLANNED"

    listing = client.get("/api/v1/runs/")
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1

    detail = client.get(f"/api/v1/runs/{run['id']}")
    assert detail.status_code == 200
    assert detail.json()["spec"]["dimension_code"] == "D01"
