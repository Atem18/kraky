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
        sleep_time: int = 5
    ) -> None:
        """
        Main function to be called.

        Arguments:
            handler: A function that will manage WS's messages
            connection_name: Give it a proper name to distinguish between the public and private WS
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
        self.connections[connection_name] = {}
        self.connections[connection_name]["closed"] = False
        self.connections[connection_name]["subscriptions"] = []
        async for websocket in websockets.connect(ws_url):
            self.connections[connection_name]["websocket"] = websocket
            try:
                # If the subscription list is already populated for this
                # connection at this point, this means the connection was
                # re-established – thus we're resubscribing to be safe.
                for subscription in self.connections[connection_name][
                    "subscriptions"
                ]:
                    self.logger.debug(
                        "Connection %s re-established - resubscribing %s.",
                        connection_name, subscription
                    )
                    await self.subscribe(
                        subscription=subscription["subscription"],
                        pair=subscription["pair"],
                        connection_name=connection_name,
                    )
                async for message in websocket:
                    data = json.loads(message)
                    if "errorMessage" in data:
                        self.logger.error(data["errorMessage"])
                    else:
                        await handler(data)
            except (
                socket.gaierror,
                websockets.exceptions.ConnectionClosed,
                ConnectionResetError
            ) as err:
                self.logger.debug(
                    "%s - retrying connection in %s sec.",
                    type(err).__name__, sleep_time
                )
                await asyncio.sleep(sleep_time)
                continue
            finally:
                if (
                    self.connections[connection_name]["websocket"].closed and
                    self.connections[connection_name]["closed"]
                ):
                    self.logger.debug("Connection successfully closed.")
                    break
        del self.connections[connection_name]
        self.logger.info(
            "Connection '%s' closed and deleted, exiting connect coroutine.",
            connection_name
        )

    async def disconnect(self, connection_name: str = "main") -> None:
        """
        Function to be called when you want to disconnect from WS

        Arguments:
            connection_name: name of the connection you want to disconnect from
        """
        if (
            connection_name in self.connections and
            "websocket" in self.connections[connection_name]
        ):
            self.logger.debug(
                "Closing websocket connection '%s'.", connection_name
            )
            self.connections[connection_name]["closed"] = True
            await self.connections[connection_name]["websocket"].close()

    async def _send(self, data: dict, connection_name: str = "main") -> None:
        while not (
            connection_name in self.connections and
            "websocket" in self.connections[connection_name]
        ):
            await asyncio.sleep(0.1)
        try:
            await self.connections[connection_name]["websocket"].send(json.dumps(data))
            await asyncio.sleep(0.1)
        except (
            socket.gaierror,
            websockets.exceptions.ConnectionClosed,
            ConnectionResetError
        ) as err:
            self.logger.debug(
                "%s - message not sent.", type(err).__name__
            )

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
            sub(r"^close_(\w+)", r"close[\1]", arg): value
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
