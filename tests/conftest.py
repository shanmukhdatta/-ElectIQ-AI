import pytest
from unittest.mock import patch

@pytest.fixture(autouse=False)
def mock_chat():
    with patch('backend.app.invoke_chat', return_value=('{"verdict":"TRUE","explanation":"Test response","sources":[]}', 'mock')):
        yield
