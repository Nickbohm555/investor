import os

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


os.environ.setdefault("INVESTOR_APP_SECRET", "test-secret")
os.environ.setdefault("INVESTOR_DATABASE_URL", "sqlite+pysqlite:///:memory:")


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())
