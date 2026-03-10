import os

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: marks tests that need a real database",
    )


def pytest_collection_modifyitems(config, items):
    test_db_url = os.environ.get("TEST_DATABASE_URL")
    if test_db_url:
        return

    skip_integration = pytest.mark.skip(reason="TEST_DATABASE_URL not set")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
