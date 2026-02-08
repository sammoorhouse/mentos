import base64
import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("TOKEN_ENCRYPTION_KEY_B64", base64.b64encode(b"0" * 32).decode())
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("APPLE_AUDIENCE", "test.audience")

from app.main import app  # noqa: E402
from app.db.session import Base, engine  # noqa: E402


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)
