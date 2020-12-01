"""Kraky websocket module"""
import asyncio
import json
import socket
from typing import Callable

import websockets

from .log import get_module_logger


class KrakyWsError(Exception):
    """Raise exception when Kraken Websocket raise an error"""


class KrakyWsClient:
    """Kraken Websocket client implementation"""

    def __init__(self, connection_env: str = "production") -> None:
        self.connection_env = connection_env
        self.connections: dict = {}
        self.logger = get_module_logger(__name__)

    async def connect(self, handler: Callable, connection_name: str = "main") -> None:
        if self.connection_env == "production":
            ws_url = "wss://ws.kraken.com"
        elif self.connection_env == "production-auth":
            ws_url = "wss://ws-auth.kraken.com"
        elif self.connection_env == "beta":
            ws_url = "wss://beta-ws.kraken.com"
        elif self.connection_env == "beta-auth":
            ws_url = "wss://beta-ws-auth.kraken.com"
        websocket = await websockets.connect(ws_url)
        self.connections[connection_name] = websocket
        while True:
            try:
                if not websocket.open:
                    websocket = await websockets.connect(ws_url)
                    self.connections[connection_name] = websocket
                else:
                    message = await websocket.recv()
                    if "errorMessage" in message:
                        error = json.loads(message)
                        self.logger.error(error["errorMessage"])
                    else:
                        data = json.loads(message)
                        await handler(data)
            except socket.gaierror:
                self.logger.error("Connection to Kraken WS closed, reconnecting...")
                continue
            except websockets.exceptions.ConnectionClosedError:
                self.logger.error("Connection to Kraken WS closed, reconnecting...")
                continue
            except websockets.exceptions.ConnectionClosedOK:
                self.logger.error("Connection to Kraken WS closed, reconnecting...")
                continue

    async def disconnect(self, connection_name: str = "main") -> None:
        if self.connections[connection_name] is not None:
            await self.connections[connection_name].close()
            del self.connections[connection_name]

    async def _sub_unsub(
        self,
        sub_type: str,
        subscription: str,
        pairs: list = None,
        connection_name: str = "main",
    ) -> None:
        while connection_name not in self.connections:
            await asyncio.sleep(0.1)
        websocket = self.connections[connection_name]
        payload: dict = {
            "event": sub_type,
            "subscription": subscription,
        }
        if pairs:
            payload["pair"] = pairs
        await websocket.send(json.dumps(payload))

    async def subscribe(
        self, subscription: str, pairs: list = None, connection_name: str = "main"
    ) -> None:
        await self._sub_unsub("subscribe", subscription, pairs, connection_name)

    async def unsubscribe(
        self, subscription: str, pairs: list = None, connection_name: str = "main"
    ) -> None:
        await self._sub_unsub("unsubscribe", subscription, pairs, connection_name)

    async def add_order(
        self,
        token: str,
        pair: str,
        type: str,
        ordertype: str,
        volume: float,
        price: float = None,
        price2: float = None,
        leverage: float = None,
        oflags: str = None,
        starttm: str = None,
        expiretm: str = None,
        userref: str = None,
        validate: str = None,
        close_ordertype: str = None,
        close_price: float = None,
        close_price2: float = None,
        trading_agreement: str = None,
        reqid: int = None,
        event: str = "addOrder",
        connection_name: str = "main",
    ) -> None:
        """https://docs.kraken.com/websockets/#message-addOrder"""
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        while connection_name not in self.connections:
            await asyncio.sleep(0.1)
        websocket = self.connections[connection_name]
        await websocket.send(json.dumps(data))
