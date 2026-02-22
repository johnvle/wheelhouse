import os

from app.config import Settings


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-anon-key")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")

    s = Settings()
    assert s.supabase_url == "https://test.supabase.co"
    assert s.supabase_anon_key == "test-anon-key"
    assert s.supabase_service_role_key == "test-service-key"
    assert s.database_url == "postgresql://localhost/test"


def test_health_endpoint():
    """Import the app and check health endpoint is registered."""
    # Set required env vars so config can load
    os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
    os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
    os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
    os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")

    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
