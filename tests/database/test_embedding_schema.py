from unittest.mock import MagicMock, patch

import pytest

from app.database.models.letter_embedding import LetterEmbedding


def test_schema_setup_commits_and_closes_without_deleting_data():
    conn = MagicMock()
    with patch('app.database.models.letter_embedding.DBConnection.get_connection', return_value=conn):
        LetterEmbedding.ensure_table()
    statements = [call.args[0].upper() for call in
                  conn.cursor.return_value.__enter__.return_value.execute.call_args_list]
    assert all('IF NOT EXISTS' in sql for sql in statements)
    assert not any(word in sql for sql in statements for word in ('TRUNCATE', 'DROP ', 'DELETE '))
    conn.commit.assert_called_once()
    conn.rollback.assert_not_called()
    conn.close.assert_called_once()


def test_schema_error_rolls_back_and_propagates():
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value.execute.side_effect = RuntimeError('schema error')
    with patch('app.database.models.letter_embedding.DBConnection.get_connection', return_value=conn):
        with pytest.raises(RuntimeError, match='schema error'):
            LetterEmbedding.ensure_table()
    conn.commit.assert_not_called()
    conn.rollback.assert_called_once()
    conn.close.assert_called_once()
