import importlib
import inspect
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException


def _load_search_service():
    # search_service loads its embedding model at import time; mock the class
    # so the (re)import doesn't require a real CUDA device.
    with patch('sentence_transformers.SentenceTransformer', return_value=MagicMock()):
        import app.api.search_service as search_service
        importlib.reload(search_service)
    return search_service


def test_search_letters_uses_shared_environment_aware_db_config():
    # LAB-009: search_service used to read config/settings.yml's hardcoded
    # "development" section directly instead of the shared settings used by
    # the rest of the app, so it ignored APP_ENV and a now-nonexistent file.
    search_service = _load_search_service()

    # The old YAML-reading helper must be gone.
    assert not hasattr(search_service, "load_db_config")

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [{"content": "x", "metadata": {}, "distance": 0.1}]

    search_service.model.encode.return_value.tolist.return_value = [0.1, 0.2]

    with patch('app.database.connection.DBConnection.get_connection', return_value=mock_conn) as mock_get_conn:
        request = search_service.QueryRequest(query="Felix", limit=3)
        result = search_service.search_letters(request)

    mock_get_conn.assert_called_once()
    assert result == {"results": [{"content": "x", "metadata": {}, "distance": 0.1}]}


def test_search_letters_is_a_plain_sync_endpoint():
    # LAB-012: search_letters does purely blocking work (model inference,
    # psycopg2) with no `await` anywhere, but was declared `async def`. That
    # runs it directly on FastAPI's single event loop instead of its
    # threadpool, so a slow request would stall every other request. A plain
    # `def` endpoint is dispatched to the threadpool by FastAPI automatically.
    search_service = _load_search_service()
    assert not inspect.iscoroutinefunction(search_service.search_letters)


def test_search_letters_closes_connection_even_when_query_fails():
    # LAB-012: the connection was only closed after a successful query, so a
    # DB error left it open/leaked.
    search_service = _load_search_service()

    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.side_effect = RuntimeError("query boom")

    search_service.model.encode.return_value.tolist.return_value = [0.1, 0.2]

    with patch('app.database.connection.DBConnection.get_connection', return_value=mock_conn):
        request = search_service.QueryRequest(query="Felix", limit=3)
        with pytest.raises(HTTPException):
            search_service.search_letters(request)

    mock_conn.close.assert_called_once()
