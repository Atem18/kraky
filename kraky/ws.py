"""Kraky websocket module"""
import asyncio
import json
import socket
from re import sub
from typing import Callable

import websockets

from .log import get_module_logger


class KrakyWsClient:
    """Kraken Websocket client implementation"""

    def __init__(
        self, connection_env: str = "production", logging_level: str = "INFO"
    ) -> None:
        """
        Initialize the object.

        Arguments:
            connection_env: https://docs.kraken.com/websockets/#connectionDetails
            logging_level: Change the log level
        """
        self.connection_env = connection_env
        self.connections: dict = {}
        self.logger = get_module_logger(__name__, logging_level)

    async def connect(
        self,
        handler: Callable,
        connection_name: str = "main",
        reply_timeout: int = 10,
        ping_timeout: int = 5,
        sleep_time: int = 5,
    ) -> None:
        """
        Main function to be called.

        Arguments:
            handler: A function that will manage WS's messages
            connection_name: Give it a proper name to distinguish between the public and private WS
            reply_timeout: Timeout after x seconds if no message on websocket
            ping_timeout: Timeout after x seconds if no pong is received
            sleep_time: Reconnects after x seconds when connection is dropped
        """
        if self.connection_env == "production":
            ws_url = "wss://ws.kraken.com"
        elif self.connection_env == "production-auth":
            ws_url = "wss://ws-auth.kraken.com"
        elif self.connection_env == "beta":
            ws_url = "wss://beta-ws.kraken.com"
        elif self.connection_env == "beta-auth":
            ws_url = "wss://beta-ws-auth.kraken.com"
        else:
            ws_url = "wss://ws.kraken.com"
        websocket = await websockets.connect(ws_url)
        self.connections[connection_name] = {}
        self.connections[connection_name]["websocket"] = websocket
        self.connections[connection_name]["subscriptions"] = []
        while True:
            try:
                if not websocket.open:
                    websocket = await websockets.connect(ws_url)
                    self.connections[connection_name]["websocket"] = websocket
                    if self.connections[connection_name]["subscriptions"]:
                        for subscription in self.connections[connection_name][
                            "subscriptions"
                        ]:
                            await self.subscribe(
                                subscription=subscription["subscription"],
                                pair=subscription["pair"],
                                connection_name=connection_name,
                            )
                else:
                    try:
                        message = await asyncio.wait_for(
                            websocket.recv(), timeout=reply_timeout
                        )
                        if "errorMessage" in message:
                            error = json.loads(message)
                            self.logger.error(error["errorMessage"])
                        else:
                            data = json.loads(message)
                            await handler(data)
                    except asyncio.TimeoutError:
                        try:
                            pong = await websocket.ping()
                            await asyncio.wait_for(pong, timeout=ping_timeout)
                            self.logger.debug("Ping OK - keeping connection alive.")
                            continue
                        except Exception as ex:
                            self.logger.error(ex)
                            self.logger.debug(
                                f"Ping error - retrying connection in {sleep_time} sec."
                            )
                            await asyncio.sleep(sleep_time)
                            break
            except socket.gaierror:
                self.logger.debug(
                    f"Socket gaia error - retrying connection in {sleep_time} sec."
                )
                await asyncio.sleep(sleep_time)
                continue
            except websockets.exceptions.ConnectionClosedError:
                self.logger.debug(
                    f"WebSockets connection closed error - retrying connection in {sleep_time} sec."
                )
                await asyncio.sleep(sleep_time)
                continue
            except websockets.exceptions.ConnectionClosedOK:
                self.logger.debug(
                    f"WebSockets connection closed ok - retrying connection in {sleep_time} sec."
                )
                await asyncio.sleep(sleep_time)
                continue
            except ConnectionResetError:
                self.logger.debug(
                    f"Connection reset error - retrying connection in {sleep_time} sec."
                )
                await asyncio.sleep(sleep_time)
                continue

    async def disconnect(self, connection_name: str = "main") -> None:
        """
        Function to be called when you want to disconnect from WS

        Arguments:
            connection_name: name of the connection you want to disconnect from
        """
        if self.connections[connection_name] is not None:
            try:
                await self.connections[connection_name]["websocket"].close()
            except socket.gaierror:
                self.logger.debug("Socket gaia error - disconnecting anyway.")
            except websockets.exceptions.ConnectionClosedError:
                self.logger.debug(
                    "WebSockets connection closed error - disconnecting anyway."
                )
            except websockets.exceptions.ConnectionClosedOK:
                self.logger.debug(
                    "WebSockets connection closed ok - disconnecting anyway."
                )
            except ConnectionResetError:
                self.logger.debug("Connection reset error - disconnecting anyway.")
            del self.connections[connection_name]

    async def _send(self, data: dict, connection_name: str = "main") -> None:
        while connection_name not in self.connections:
            await asyncio.sleep(0.1)
        try:
            await self.connections[connection_name]["websocket"].send(json.dumps(data))
            await asyncio.sleep(0.1)
        except socket.gaierror:
            self.logger.debug("Socket gaia error - message not sent.")
        except websockets.exceptions.ConnectionClosedError:
            self.logger.debug("WebSockets connection closed error - message not sent.")
        except websockets.exceptions.ConnectionClosedOK:
            self.logger.debug("WebSockets connection closed ok - message not sent.")
        except ConnectionResetError:
            self.logger.debug("Connection reset error - message not sent.")

    async def ping(self, reqid: int = None, connection_name: str = "main") -> None:
        """
        https://docs.kraken.com/websockets/#message-ping
        https://docs.kraken.com/websockets/#message-pong

        Arguments:
            requid: Optional - client originated ID reflected in response message
            connection_name: Name of the connection you want to ping
        """
        data: dict = {}
        data["event"] = "ping"
        if reqid:
            data["reqid"] = reqid
        await self._send(data=data, connection_name=connection_name)

    async def _sub_unsub(
        self,
        event: str,
        subscription: dict,
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
        subscription: dict,
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
        """
        await self._sub_unsub(
            event="subscribe",
            subscription=subscription,
            pair=pair,
            reqid=reqid,
            connection_name=connection_name,
        )
        self.connections[connection_name]["subscriptions"].append(
            {"event": "subscribe", "pair": pair, "subscription": subscription}
        )

    async def unsubscribe(
        self,
        subscription: dict,
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
            sub("^close_(\w+)", r"close[\1]", arg): value
            for arg, value in locals().items()
            if arg != "self" and arg != "connection_name" and value is not None
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
            if arg != "self" and arg != "connection_name" and value is not None
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
            if arg != "self" and arg != "connection_name" and value is not None
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
            if arg != "self" and arg != "connection_name" and value is not None
        }
        await self._send(data=data, connection_name=connection_name)
