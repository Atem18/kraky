"""Kraky websocket module"""
import asyncio
import json
import socket
from typing import Callable

import websockets

from .log import get_module_logger


class KrakyWsError(Exception):
    """Raise exception when Kraken's Websocket raise an error"""


class KrakyWsClient:
    """Kraken Websocket client implementation"""

    def __init__(self, connection_env: str = "production") -> None:
        """
        Initialize the object.

        Arguments:
            connection_env: https://docs.kraken.com/websockets/#connectionDetails
        """
        self.connection_env = connection_env
        self.connections: dict = {}
        self.logger = get_module_logger(__name__)

    async def connect(self, handler: Callable, connection_name: str = "main") -> None:
        """
        Main function to be called.

        Arguments:
            handler: A function that will manage WS's messages
            connection_name: Give it a proper name to distinguish between the public and private WS
        """
        if self.connection_env == "production":
            ws_url = "wss://ws.kraken.com"
        elif self.connection_env == "production-auth":
            ws_url = "wss://ws-auth.kraken.com"
        elif self.connection_env == "beta":
            ws_url = "wss://beta-ws.kraken.com"
        elif self.connection_env == "beta-auth":
            ws_url = "wss://beta-ws-auth.kraken.com"
        websocket = await websockets.connect(ws_url)
        self.connections[connection_name]["websocket"] = websocket
        self.connections[connection_name]["subscriptions"] = []
        while True:
            try:
                if not websocket.open:
                    websocket = await websockets.connect(ws_url)
                    self.connections[connection_name]["websocket"] = websocket
                    if self.connections[connection_name]["subscriptions"]:
                        for subscription in self.connections[connection_name]["subscriptions"]:
                            await self.subscribe(subscription=subscription["subscription"], pair=subscription["pair"], connection_name=connection_name)
                else:
                    message = await websocket.recv()
                    if "errorMessage" in message:
                        error = json.loads(message)
                        self.logger.error(error["errorMessage"])
                    else:
                        data = json.loads(message)
                        await handler(data)
            except socket.gaierror:
                continue
            except websockets.exceptions.ConnectionClosedError:
                continue
            except websockets.exceptions.ConnectionClosedOK:
                continue

    async def disconnect(self, connection_name: str = "main") -> None:
        """
        Function to be called when you want to disconnect from WS

        Arguments:
            connection_name: name of the connection you want to disconnect from
        """
        if self.connections[connection_name] is not None:
            await self.connections[connection_name]["websocket"].close()
            del self.connections[connection_name]

    async def _send(self, data: dict, connection_name: str = "main") -> None:
        while connection_name not in self.connections:
            await asyncio.sleep(0.1)
        websocket = self.connections[connection_name]["websocket"]
        try:
            await websocket.send(json.dumps(data))
        except socket.gaierror:
            raise KrakyWsError
        except websockets.exceptions.ConnectionClosedError:
            raise KrakyWsError
        except websockets.exceptions.ConnectionClosedOK:
            raise KrakyWsError

    async def ping(self, reqid: int = None, connection_name: str = "main") -> None:
        """
        https://docs.kraken.com/websockets/#message-ping
        https://docs.kraken.com/websockets/#message-pong

        Arguments:
            requid: Optional - client originated ID reflected in response message
            connection_name: Name of the connection you want to ping

        Raises:
            KrakyWsError: If the connection has an issue
        """
        await self._send(
            data={"event": "ping", "reqid": reqid}, connection_name=connection_name
        )

    async def _sub_unsub(
        self,
        event: str,
        subscription: str,
        pair: list = None,
        reqid: int = None,
        connection_name: str = "main",
    ) -> None:
        data: dict = {
            "event": event,
            "subscription": subscription,
        }
        if pair:
            data["pair"] = pair
        if reqid:
            data["reqid"] = reqid
        await self._send(data=data, connection_name=connection_name)

    async def subscribe(
        self,
        subscription: str,
        pair: list = None,
        reqid: int = None,
        connection_name: str = "main",
    ) -> None:
        """
        https://docs.kraken.com/websockets/#message-subscribe

        Arguments:
            subscription: Subscribe to a topic on a single or multiple currency pairs.
            pair: Optional - Array of currency pairs. Format of each pair is "A/B", where A and B are ISO 4217-A3 for standardized assets and popular unique symbol if not standardized.
            reqid: Optional - client originated ID reflected in response message
            connection_name: name of the connection you want to subscribe to

        Raises:
            KrakyWsError: If the connection has an issue
        """
        await self._sub_unsub(
            event="subscribe",
            subscription=subscription,
            pair=pair,
            reqid=reqid,
            connection_name=connection_name,
        )

    async def unsubscribe(
        self,
        subscription: str,
        pair: list = None,
        reqid: int = None,
        connection_name: str = "main",
    ) -> None:
        """
        https://docs.kraken.com/websockets/#message-subscribe

        Arguments:
            subscription: Subscribe to a topic on a single or multiple currency pairs.
            pair: Optional - Array of currency pairs. Format of each pair is "A/B", where A and B are ISO 4217-A3 for standardized assets and popular unique symbol if not standardized.
            reqid: Optional - client originated ID reflected in response message
            connection_name: name of the connection you want to subscribe to

        Raises:
            KrakyWsError: If the connection has an issue
        """
        await self._sub_unsub(
            event="unsubscribe",
            subscription=subscription,
            pair=pair,
            reqid=reqid,
            connection_name=connection_name,
        )

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
        await self._send(data=data, connection_name=connection_name)

    async def cancel_order(
        self,
        token: str,
        txid: list,
        reqid: int = None,
        event: str = "cancelOrder",
        connection_name: str = "main",
    ) -> None:
        """https://docs.kraken.com/websockets/#message-cancelOrder"""
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        await self._send(data=data, connection_name=connection_name)

    async def cancel_all(
        self,
        token: str,
        reqid: int = None,
        event: str = "cancelAll",
        connection_name: str = "main",
    ) -> None:
        """https://docs.kraken.com/websockets/#message-cancelAll"""
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        await self._send(data=data, connection_name=connection_name)

    async def cancel_all_orders_after(
        self,
        token: str,
        timeout: int,
        reqid: int = None,
        event: str = "cancelAllOrdersAfter",
        connection_name: str = "main",
    ) -> None:
        """https://docs.kraken.com/websockets/#message-cancelAllOrdersAfter"""
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        await self._send(data=data, connection_name=connection_name)
