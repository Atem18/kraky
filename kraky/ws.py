"""Kraky websocket module"""
import asyncio
import json
import socket
from re import sub
from typing import Callable, Optional

import websockets

from kraky.log import get_module_logger


class KrakyWsClient:
    """Kraken Websocket client implementation"""

    def __init__(
        self, connection_env: str = "production", logging_level: str = "INFO"
    ) -> None:
        """
        Arguments:
            connection_env: Predefined environment strings (production[-auth] and beta[-auth])
                will be mapped to the corresponding URLs, otherwise the string is
                taken as it is as target URL. https://docs.kraken.com/websockets/#connectionDetails
            logging_level: Change the log level
        """
        self.connection_env = connection_env
        self.connections: dict = {}
        self.logger = get_module_logger(__name__, logging_level)

    async def connect(
        self, handler: Callable, connection_name: str = "main", sleep_time: int = 5
    ) -> None:
        """
        Connect to the websocket and start the handler coroutine.

        Arguments:
            handler: coroutine that will handle the incoming messages
            connection_name: name of the connection you want to subscribe to
            sleep_time: time to wait before retrying to connect
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
            ws_url = self.connection_env
        self.connections[connection_name] = {}
        self.connections[connection_name]["closed"] = False
        self.connections[connection_name]["subscriptions"] = []
        async for websocket in websockets.connect(ws_url):
            self.connections[connection_name]["websocket"] = websocket
            try:
                # If the subscription list is already populated for this
                # connection at this point, this means the connection was
                # re-established – thus we're resubscribing to be safe.
                for subscription in self.connections[connection_name]["subscriptions"]:
                    self.logger.debug(
                        "Connection %s re-established - resubscribing %s.",
                        connection_name,
                        subscription,
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
                ConnectionResetError,
            ) as err:
                self.logger.debug(
                    "%s - retrying connection in %s sec.",
                    type(err).__name__,
                    sleep_time,
                )
                await asyncio.sleep(sleep_time)
                continue
            finally:
                if (
                    self.connections[connection_name]["websocket"].closed
                    and self.connections[connection_name]["closed"]
                ):
                    self.logger.debug("Connection successfully closed.")
                    break
                continue
        del self.connections[connection_name]
        self.logger.info(
            "Connection '%s' closed and deleted, exiting connect coroutine.",
            connection_name,
        )

    async def disconnect(self, connection_name: str = "main") -> None:
        """
        Close the websocket connection.

        Arguments:
            connection_name: name of the connection you want to subscribe to
        """
        if (
            connection_name in self.connections
            and "websocket" in self.connections[connection_name]
        ):
            self.logger.debug("Closing websocket connection '%s'.", connection_name)
            self.connections[connection_name]["closed"] = True
            await self.connections[connection_name]["websocket"].close()

    async def _send(self, data: dict, connection_name: str = "main") -> None:
        """Internal function to send data to WS"""
        while not (
            connection_name in self.connections
            and "websocket" in self.connections[connection_name]
        ):
            await asyncio.sleep(0.1)
        try:
            await self.connections[connection_name]["websocket"].send(json.dumps(data))
            await asyncio.sleep(0.1)
        except (
            socket.gaierror,
            websockets.exceptions.ConnectionClosed,
            ConnectionResetError,
        ) as err:
            self.logger.debug("%s - message not sent.", type(err).__name__)

    async def ping(
        self, reqid: Optional[int] = None, connection_name: str = "main"
    ) -> None:
        """
        https://docs.kraken.com/websockets/#message-ping
        https://docs.kraken.com/websockets/#message-pong

        Arguments:
            reqid: Optional - client originated ID reflected in response message
            connection_name: name of the connection you want to subscribe to
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
        pair: Optional[list] = None,
        reqid: Optional[int] = None,
        connection_name: str = "main",
    ) -> None:
        """
        Internal function to subscribe or unsubscribe to a topic on a single or multiple currency pairs.
        Arguments:
            event: subscribe or unsubscribe
            subscription: Subscribe to a topic on a single or multiple currency pairs.
            pair: Optional - Array of currency pairs. Format of each pair is "A/B", where A and B are ISO 4217-A3 for standardized assets and popular unique symbol if not standardized.
            reqid: Optional - client originated ID reflected in response message
            connection_name: name of the connection you want to subscribe to
        """
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
        pair: Optional[list] = None,
        reqid: Optional[int] = None,
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
        pair: Optional[list] = None,
        reqid: Optional[int] = None,
        connection_name: str = "main",
    ) -> None:
        """
        https://docs.kraken.com/websockets/#message-subscribe

        Arguments:
            subscription: Unsubscribe from a topic on a single or multiple currency pairs.
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
        price: Optional[float] = None,
        price2: Optional[float] = None,
        leverage: Optional[float] = None,
        reduce_only: Optional[bool] = None,
        oflags: Optional[str] = None,
        starttm: Optional[str] = None,
        expiretm: Optional[str] = None,
        userref: Optional[str] = None,
        validate: Optional[str] = None,
        close_ordertype: Optional[str] = None,
        close_price: Optional[float] = None,
        close_price2: Optional[float] = None,
        timeinforce: Optional[str] = None,
        reqid: Optional[int] = None,
        event: str = "addOrder",
        connection_name: str = "main",
    ) -> None:
        """
        https://docs.kraken.com/websockets/#message-addOrder

        Arguments:
            token: Authentication token
            pair: Asset pair
            type: Type of order (buy/sell)
            ordertype: Order type:
                market
                limit (price = limit price)
                stop-loss (price = stop loss price)
                take-profit (price = take profit price)
                stop-loss-profit (price = stop loss price, price2 = take profit price)
                stop-loss-profit-limit (price = stop loss price, price2 = take profit price)
                stop-loss-limit (price = stop loss trigger price, price2 = triggered limit price)
                take-profit-limit (price = take profit trigger price, price2 = triggered limit price)
                trailing-stop (price = trailing stop offset)
                trailing-stop-limit (price = trailing stop offset, price2 = triggered limit offset)
                stop-loss-and-limit (price = stop loss price, price2 = limit price)
                settle-position
            volume: Order volume in lots
            price: Price (optional.  dependent upon ordertype)
            price2: Secondary price (optional.  dependent upon ordertype)
            leverage: Amount of leverage desired (optional.  default = none)
            reduce_only: Indicates that the order should only reduce an existing position (optional.  default = false)
            oflags: Comma delimited list of order flags (optional):
                viqc = volume in quote currency (not available for leveraged orders)
                fcib = prefer fee in base currency
                fciq = prefer fee in quote currency
                nompp = no market price protection
                post = post only order (available when ordertype = limit)
            starttm: Scheduled start time (optional):
                0 = now (default)
                +<n> = schedule start time <n> seconds from now
                <n> = unix timestamp of start time
            expiretm: Expiration time (optional):
                0 = no expiration (default)
                +<n> = expire <n> seconds from now
                <n> = unix timestamp of expiration time
            userref: User reference id.  32-bit signed number.  (optional)
            validate: Validate inputs only.  do not submit order (optional)
            close_ordertype: Order type:
                limit (price = limit price)
                stop-loss (price = stop loss price)
                take-profit (price = take profit price)
                stop-loss-profit (price = stop loss price, price2 = take profit price)
                stop-loss-profit-limit (price = stop loss price, price2 = take profit price)
                stop-loss-limit (price = stop loss trigger price, price2 = triggered limit price)
                take-profit-limit (price = take profit trigger price, price2 = triggered limit price)
                trailing-stop (price = trailing stop offset)
                trailing-stop-limit (price = trailing stop offset, price2 = triggered limit offset)
                stop-loss-and-limit (price = stop loss price, price2 = limit price)
                settle-position
            close_price: Secondary price (optional.  dependent upon ordertype)
            close_price2: Secondary price (optional.  dependent upon ordertype)
            timeinforce: Time in force.  (optional)
                GTC = Good till cancelled (default)
                IOC = Immediate or cancel
                FOK = Fill or kill
            reqid: Optional - client originated ID reflected in response message
            connection_name: name of the connection you want to subscribe to
        """
        data = {
            sub(r"^close_(\w+)", r"close[\1]", arg): value
            for arg, value in locals().items()
            if arg != "self" and arg != "connection_name" and value is not None
        }
        await self._send(data=data, connection_name=connection_name)

    async def edit_order(
        self,
        token: str,
        orderid: list,
        pair: str,
        volume: float,
        price: Optional[float] = None,
        price2: Optional[float] = None,
        oflags: Optional[str] = None,
        newuserref: Optional[str] = None,
        validate: Optional[str] = None,
        reqid: Optional[int] = None,
        event: str = "editOrder",
        connection_name: str = "main",
    ):
        """
        https://docs.kraken.com/websockets/#message-editOrder

        Arguments:
            token: Authentication token
            orderid: Order id
            pair: Asset pair
            volume: Order volume in lots
            price: Price (optional.  dependent upon ordertype)
            price2: Secondary price (optional.  dependent upon ordertype)
            oflags: Comma delimited list of order flags (optional):
                viqc = volume in quote currency (not available for leveraged orders)
                fcib = prefer fee in base currency
                fciq = prefer fee in quote currency
                nompp = no market price protection
                post = post only order (available when ordertype = limit)
            newuserref: Updated user reference id.  32-bit signed number.  (optional)
            validate: Validate inputs only.  do not submit order (optional)
            reqid: Optional - client originated ID reflected in response message
            connection_name: name of the connection you want to subscribe to
        """
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
        reqid: Optional[int] = None,
        event: str = "cancelOrder",
        connection_name: str = "main",
    ) -> None:
        """
        https://docs.kraken.com/websockets/#message-cancelOrder

        Arguments:
            token: Authentication token
            txid: Transaction id
            reqid: Optional - client originated ID reflected in response message
            connection_name: name of the connection you want to subscribe to
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and arg != "connection_name" and value is not None
        }
        await self._send(data=data, connection_name=connection_name)

    async def cancel_all(
        self,
        token: str,
        reqid: Optional[int] = None,
        event: str = "cancelAll",
        connection_name: str = "main",
    ) -> None:
        """
        https://docs.kraken.com/websockets/#message-cancelAll

        Arguments:
            token: Authentication token
            reqid: Optional - client originated ID reflected in response message
            connection_name: name of the connection you want to subscribe to
        """
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
        reqid: Optional[int] = None,
        event: str = "cancelAllOrdersAfter",
        connection_name: str = "main",
    ) -> None:
        """
        https://docs.kraken.com/websockets/#message-cancelAllOrdersAfter

        Arguments:
            token: Authentication token
            timeout: Timeout in seconds. 0 = cancel timer (optional)
            reqid: Optional - client originated ID reflected in response message
            connection_name: name of the connection you want to subscribe to
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and arg != "connection_name" and value is not None
        }
        await self._send(data=data, connection_name=connection_name)
