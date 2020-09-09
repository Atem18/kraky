"""Kraky websocket module"""
import asyncio
import json
import websockets
from .log import get_module_logger


class KrakyWsError(Exception):
    pass


class KrakyWsClient:
    def __init__(self, connection_env="production"):
        self.connection_env = connection_env
        self.connections = {}
        self.logger = get_module_logger(__name__)

    async def connect(self, handler, connection_name="main"):
        if self.connection_env == "production":
            ws_url = "wss://ws.kraken.com"
        elif self.connection_env == "production-auth":
            ws_url = "wss://ws-auth.kraken.com"
        elif self.connection_env == "beta":
            ws_url = "wss://beta-ws.kraken.com"
        elif self.connection_env == "beta-auth":
            ws_url = "wss://beta-ws-auth.kraken.com"
        async with websockets.connect(ws_url) as ws:
            self.connections[connection_name] = ws
            async for msg in ws:
                if "errorMessage" in msg:
                    error = json.loads(msg)
                    self.logger.error(error["errorMessage"])
                else:
                    data = json.loads(msg)
                    await handler(data)

    async def disconnect(self, connection_name="main"):
        if self.connections[connection_name] is not None:
            await self.connections[connection_name].close()
            del self.connections[connection_name]

    async def _sub_unsub(
        self, sub_type, subscription, pairs=None, connection_name="main"
    ):
        while connection_name not in self.connections:
            await asyncio.sleep(1)
        ws = self.connections[connection_name]
        payload = {
            "event": sub_type,
            "subscription": subscription,
        }
        if pairs:
            payload["pair"] = pairs
        try:
            await ws.send(json.dumps(payload))
        except websockets.exceptions.ConnectionClosedError as err:
            self.logger.exception(str(err))

    async def subscribe(self, subscription, pairs=None, connection_name="main"):
        await self._sub_unsub("subscribe", subscription, pairs, connection_name)

    async def unsubscribe(
        self, subscription, pairs=None, connection_name="main"
    ):
        await self._sub_unsub(
            "unsubscribe", subscription, pairs, connection_name
        )
