import pytest
import logging
from app.core.logger import setup_logging

@pytest.fixture(scope="session", autouse=True)
def configure_test_logging():
    # This runs once before all tests
    setup_logging()
