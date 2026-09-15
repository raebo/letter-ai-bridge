import importlib
import inspect
from unittest.mock import MagicMock, patch


def _load_chat_service():
    # chat_service loads its embedding model at import time; mock the class
    # so the (re)import doesn't require a real CUDA device.
    with patch('sentence_transformers.SentenceTransformer', return_value=MagicMock()):
        import app.api.chat_service as chat_service
        importlib.reload(chat_service)
    return chat_service


def test_chat_with_mendelssohn_is_a_plain_sync_endpoint():
    # LAB-012: chat_with_mendelssohn does purely blocking work (embedding
    # model, DB lookups via the model classes, Ollama) with no `await`
    # anywhere, but was declared `async def`. That runs it directly on
    # FastAPI's single event loop instead of its threadpool, so one slow
    # chat request would stall every other request (search included). A
    # plain `def` endpoint is dispatched to the threadpool automatically.
    chat_service = _load_chat_service()
    assert not inspect.iscoroutinefunction(chat_service.chat_with_mendelssohn)
