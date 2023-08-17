import json
import pytest
from typing import Callable

async def _ws_handler(websocket) -> None:
    global last_ws_msg
    async for message in websocket:
        pytest.last_ws_msg = json.loads(message)


@pytest.fixture
def ws_handler() -> Callable:
    return _ws_handler


@pytest.fixture
def ws_host() -> str:
    return "localhost"


@pytest.fixture
def ws_port() -> int:
    return 5555


@pytest.fixture
def ws_url() -> str:
    return "ws://localhost:5555"