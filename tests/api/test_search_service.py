import asyncio
import importlib
from unittest.mock import MagicMock, patch


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
        result = asyncio.run(search_service.search_letters(request))

    mock_get_conn.assert_called_once()
    assert result == {"results": [{"content": "x", "metadata": {}, "distance": 0.1}]}
