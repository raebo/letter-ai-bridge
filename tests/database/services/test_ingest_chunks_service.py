from unittest.mock import MagicMock, patch
import pytest

from app.database.services.ingest_chunks_service import IngestChunksService


def _make_service_with_mock_conn():
    mock_conn = MagicMock()
    with patch('app.database.connection.DBConnection.get_connection', return_value=mock_conn):
        service = IngestChunksService()
    return service, mock_conn


def test_upload_chunks_success_commits():
    service, mock_conn = _make_service_with_mock_conn()
    chunks = [{"letter_id": 1, "content": "text", "metadata": {}, "vector": [0.1, 0.2]}]

    service.upload_chunks(chunks)

    mock_conn.commit.assert_called_once()
    mock_conn.rollback.assert_not_called()


def test_upload_chunks_propagates_db_error_instead_of_swallowing_it():
    # LAB-008: a failed executemany used to be caught, rolled back and only
    # printed, so upload_chunks returned None like on success and callers
    # (e.g. scripts/process_letters.py) never learned the letter failed.
    service, mock_conn = _make_service_with_mock_conn()
    mock_conn.cursor.return_value.__enter__.return_value.executemany.side_effect = RuntimeError("boom")
    chunks = [{"letter_id": 1, "content": "text", "metadata": {}, "vector": [0.1, 0.2]}]

    with pytest.raises(RuntimeError, match="boom"):
        service.upload_chunks(chunks)

    mock_conn.rollback.assert_called_once()
    mock_conn.commit.assert_not_called()
