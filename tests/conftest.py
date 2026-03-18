import os
from dotenv import load_dotenv

def pytest_configure(config):
    """
    Load environment variables from .env before running tests.
    """
    load_dotenv(override=True)
