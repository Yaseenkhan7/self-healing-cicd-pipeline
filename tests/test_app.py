"""
Test suite for the demo Flask application.
Run with:  pytest tests/ -v --cov=app
"""

import pytest
import sys
import os

# Ensure the app package is importable regardless of working directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import main as app_module  # noqa: E402 – import after path manipulation


# --------------------------------------------------------------------------- #
#  Fixtures                                                                    #
# --------------------------------------------------------------------------- #

@pytest.fixture()
def client():
    """Return a test client for the Flask application."""
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c


# --------------------------------------------------------------------------- #
#  Route tests                                                                 #
# --------------------------------------------------------------------------- #

class TestIndexRoute:
    def test_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_html_content_type(self, client):
        resp = client.get("/")
        assert "text/html" in resp.content_type

    def test_page_contains_branding(self, client):
        resp = client.get("/")
        body = resp.data.decode()
        assert "Self-Healing" in body


class TestHealthEndpoint:
    def test_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_json_content_type(self, client):
        resp = client.get("/health")
        assert resp.content_type == "application/json"

    def test_status_field_is_healthy(self, client):
        data = client.get("/health").get_json()
        assert data["status"] == "healthy"

    def test_version_field_present(self, client):
        data = client.get("/health").get_json()
        assert "version" in data

    def test_uptime_is_non_negative(self, client):
        data = client.get("/health").get_json()
        assert data["uptime_seconds"] >= 0

    def test_timestamp_field_present(self, client):
        data = client.get("/health").get_json()
        assert "timestamp" in data


class TestMetricsEndpoint:
    def test_returns_200(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 200

    def test_plaintext_content_type(self, client):
        resp = client.get("/metrics")
        assert "text/plain" in resp.content_type

    def test_contains_uptime_metric(self, client):
        body = client.get("/metrics").data.decode()
        assert "app_uptime_seconds" in body

    def test_contains_app_info_metric(self, client):
        body = client.get("/metrics").data.decode()
        assert "app_info" in body


class TestApiStatusEndpoint:
    def test_returns_200(self, client):
        resp = client.get("/api/status")
        assert resp.status_code == 200

    def test_ready_field_is_true(self, client):
        data = client.get("/api/status").get_json()
        assert data["ready"] is True

    def test_service_name_present(self, client):
        data = client.get("/api/status").get_json()
        assert data["service"] == "self-healing-cicd-demo"


class TestErrorHandlers:
    def test_404_returns_json(self, client):
        resp = client.get("/this/path/does/not/exist")
        assert resp.status_code == 404
        data = resp.get_json()
        assert "error" in data

    def test_404_includes_path(self, client):
        resp = client.get("/nonexistent")
        data = resp.get_json()
        assert data.get("path") == "/nonexistent"
