"""
Pytest configuration and fixtures for Order Processing spec tests.

Spec reference: /openspec/features/order-processing.md

The app import is deferred to the client fixture so tests are discoverable.
Tests will fail when run until app.main implements the FastAPI application.
"""

import pytest
from fastapi.testclient import TestClient

import sys
from pathlib import Path

from app.main import app

# Ensure project root is on PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


@pytest.fixture
def client() -> TestClient:
    """HTTP client for testing API endpoints."""
    from app.main import app  # Fails until app is implemented
    return TestClient(app)


@pytest.fixture
def base_path() -> str:
    """Base API path per spec section 3."""
    return "/api/v1"
