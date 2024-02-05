import asyncio
import pytest
import random
import string
import websockets

from kraky import KrakyWsClient


def test_client(ws_url):
    wsc = KrakyWsClient(connection_env=ws_url)
    assert wsc.connection_env == ws_url
    assert not wsc.connections


@pytest.mark.asyncio
async def test_send(ws_handler, ws_host, ws_port, ws_url):
    async with websockets.serve(ws_handler, ws_host, ws_port):
        wsc = KrakyWsClient(connection_env=ws_url)
        asyncio.create_task(wsc.connect(None))
        await asyncio.sleep(1)
        characters = string.ascii_letters + string.digits + string.punctuation
        msgs = [
            {
                "".join(random.choice(characters) for i in range(8)): "".join(
                    random.choice(characters) for i in range(8)
                )
            }
            for i in range(1000)
        ]
        assert "main" in wsc.connections
        assert "websocket" in wsc.connections["main"]
        assert wsc.connections["main"]["websocket"].open
        await wsc.disconnect()


@pytest.mark.asyncio
async def test_connect_disconnect(ws_handler, ws_host, ws_port, ws_url):
    async with websockets.serve(ws_handler, ws_host, ws_port):
        wsc = KrakyWsClient(connection_env=ws_url)
        asyncio.create_task(wsc.connect(None))
        await asyncio.sleep(1)
        assert "main" in wsc.connections
        assert "websocket" in wsc.connections["main"]
        assert wsc.connections["main"]["websocket"].open
        await wsc.disconnect()
        await asyncio.sleep(1)
        assert "main" not in wsc.connections


@pytest.mark.asyncio
async def test_subscribe(ws_handler, ws_host, ws_port, ws_url):
    async with websockets.serve(ws_handler, ws_host, ws_port):
        wsc = KrakyWsClient(connection_env=ws_url)
        asyncio.create_task(wsc.connect(None))
        await asyncio.sleep(1)
        ws_pairs = ["XBT/USD", "ETH/USD"]
        await wsc.subscribe(
            subscription={"name": "ohlc", "interval": 30}, pair=ws_pairs
        )
        exp_sub = {
            "event": "subscribe",
            "subscription": {"name": "ohlc", "interval": 30},
            "pair": ["XBT/USD", "ETH/USD"],
        }
        assert wsc.connections["main"]["subscriptions"]
        assert wsc.connections["main"]["subscriptions"][-1] == exp_sub
        assert pytest.last_ws_msg == exp_sub
        await wsc.disconnect()


@pytest.mark.asyncio
async def test_unsubscribe(ws_handler, ws_host, ws_port, ws_url):
    async with websockets.serve(ws_handler, ws_host, ws_port):
        wsc = KrakyWsClient(connection_env=ws_url)
        asyncio.create_task(wsc.connect(None))
        await asyncio.sleep(1)
        ws_pairs = ["XBT/USD", "ETH/USD"]
        test_sub = {
            "event": "subscribe",
            "subscription": {"name": "ohlc", "interval": 30},
            "pair": ["XBT/USD", "ETH/USD"],
        }
        wsc.connections["main"]["subscriptions"].append(test_sub)
        await wsc.unsubscribe(
            subscription={"name": "ohlc", "interval": 30}, pair=ws_pairs
        )
        exp_unsub = {
            "event": "unsubscribe",
            "subscription": {"name": "ohlc", "interval": 30},
            "pair": ["XBT/USD", "ETH/USD"],
        }
        assert pytest.last_ws_msg == exp_unsub
        await wsc.disconnect()
