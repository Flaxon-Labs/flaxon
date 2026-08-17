import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any, AsyncGenerator, Generator

import pytest

from flaxon import Flaxon
from flaxon.database import DatabaseManager, PostgresConnection, SQLiteConnection
from flaxon.database.adapters.sqlite import SQLiteAdapter
from flaxon.testing import TestClient


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def app() -> Flaxon:
    """Create a test application instance."""
    app = Flaxon("test-app", debug=True)
    return app


@pytest.fixture
def client(app: Flaxon) -> TestClient:
    """Create a test client for the application."""
    return TestClient(app)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_db_path() -> Generator[str, None, None]:
    """Create a temporary SQLite database path."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
async def sqlite_db(temp_db_path: str) -> AsyncGenerator[DatabaseManager, None]:
    """Create a SQLite database manager for testing."""
    adapter = SQLiteAdapter(database=temp_db_path)
    pool = DatabaseManager(adapter)
    await pool.initialize()
    yield pool
    await pool.close()


@pytest.fixture
def sample_data() -> dict[str, Any]:
    """Return sample data for testing."""
    return {
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com", "age": 25},
            {"id": 2, "name": "Bob", "email": "bob@example.com", "age": 30},
            {"id": 3, "name": "Charlie", "email": "charlie@example.com", "age": 35},
        ],
        "products": [
            {"id": 1, "name": "Laptop", "price": 999.99},
            {"id": 2, "name": "Mouse", "price": 19.99},
            {"id": 3, "name": "Keyboard", "price": 49.99},
        ],
    }


@pytest.fixture
def validation_schemas() -> dict[str, Any]:
    """Return sample validation schemas for testing."""
    from flaxon.validation import Schema, fields

    class UserCreate(Schema):
        name = fields.StrField(required=True, min_length=2, max_length=80)
        email = fields.Email(required=True)
        age = fields.Integer(required=False, minimum=13, maximum=120)

    class UserUpdate(Schema):
        name = fields.StrField(required=False, min_length=2, max_length=80)
        email = fields.Email(required=False)
        age = fields.Integer(required=False, minimum=13, maximum=120)

    return {
        "UserCreate": UserCreate,
        "UserUpdate": UserUpdate,
    }


@pytest.fixture
def mock_headers() -> dict[str, str]:
    """Return mock headers for testing."""
    return {
        "User-Agent": "TestClient/1.0",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }


@pytest.fixture
def mock_query_params() -> dict[str, Any]:
    """Return mock query parameters for testing."""
    return {
        "page": 1,
        "per_page": 20,
        "sort": "name",
        "order": "asc",
        "filter": "active",
    }


@pytest.fixture
def mock_path_params() -> dict[str, Any]:
    """Return mock path parameters for testing."""
    return {
        "user_id": 42,
        "product_id": 123,
        "slug": "test-slug",
    }


@pytest.fixture
def mock_request_data() -> dict[str, Any]:
    """Return mock request data for testing."""
    return {
        "name": "Test User",
        "email": "test@example.com",
        "password": "SecurePass123!",
        "age": 25,
    }


@pytest.fixture
def mock_response_data() -> dict[str, Any]:
    """Return mock response data for testing."""
    return {
        "success": True,
        "data": {
            "id": 1,
            "name": "Test User",
            "email": "test@example.com",
            "created_at": "2024-01-01T00:00:00Z",
        },
    }


@pytest.fixture
def mock_error_response() -> dict[str, Any]:
    """Return mock error response for testing."""
    return {
        "success": False,
        "error": {
            "code": "FX-VAL-001",
            "message": "Validation failed",
            "fields": {
                "email": ["Enter a valid email address."],
            },
        },
    }


@pytest.fixture
def mock_websocket_messages() -> list[dict[str, Any]]:
    """Return mock WebSocket messages for testing."""
    return [
        {"type": "ping", "data": {"timestamp": "2024-01-01T00:00:00Z"}},
        {"type": "message", "data": {"text": "Hello, world!"}},
        {"type": "typing", "data": {"user": "alice", "is_typing": True}},
        {"type": "pong", "data": {"timestamp": "2024-01-01T00:00:01Z"}},
    ]


@pytest.fixture
def mock_task_data() -> dict[str, Any]:
    """Return mock task data for testing."""
    return {
        "name": "test_task",
        "args": [1, 2, 3],
        "kwargs": {"param": "value"},
        "queue": "default",
        "priority": 0,
    }


@pytest.fixture
def mock_cache_data() -> dict[str, Any]:
    """Return mock cache data for testing."""
    return {
        "key": "test_key",
        "value": {"data": "test_value", "meta": {"version": 1}},
        "ttl": 60,
    }


@pytest.fixture
def mock_session_data() -> dict[str, Any]:
    """Return mock session data for testing."""
    return {
        "user_id": 1,
        "username": "testuser",
        "role": "admin",
        "permissions": ["read", "write", "delete"],
    }


@pytest.fixture
def mock_file_upload() -> dict[str, Any]:
    """Return mock file upload data for testing."""
    return {
        "filename": "test_file.txt",
        "content": b"Hello, world!",
        "content_type": "text/plain",
        "size": 13,
    }


@pytest.fixture
def mock_email_data() -> dict[str, Any]:
    """Return mock email data for testing."""
    return {
        "from_address": "sender@example.com",
        "to": ["recipient@example.com"],
        "subject": "Test Email",
        "body": "This is a test email.",
        "html_body": "<h1>Test Email</h1><p>This is a test email.</p>",
    }


@pytest.fixture
def mock_metrics_data() -> dict[str, Any]:
    """Return mock metrics data for testing."""
    return {
        "requests_total": 100,
        "errors_total": 5,
        "duration_ms": 150.5,
        "active_connections": 10,
    }


@pytest.fixture
def mock_plugin_metadata() -> dict[str, Any]:
    """Return mock plugin metadata for testing."""
    return {
        "name": "test-plugin",
        "version": "1.0.0",
        "description": "A test plugin",
        "author": "Test Author",
        "requires": ["core"],
        "provides": ["test-feature"],
    }