"""Kraky API module for Kraken's API implementation"""
import base64
import hashlib
import hmac
import urllib
import time

import httpx

from .log import get_module_logger


class KrakyApiError(Exception):
    """Raise an exception when Kraken's API raise an error"""


class KrakyApiClient:
    """Kraken API client implementation"""

    def __init__(self, api_key: str = "", secret: str = "") -> None:
        self.base_url = "https://api.kraken.com"
        self.api_key = api_key
        self.secret = secret
        self.logger = get_module_logger(__name__)

    def _sign_message(self, api_path: str, data: dict) -> str:
        post_data = urllib.parse.urlencode(data)
        encoded = (str(data["nonce"]) + post_data).encode()
        message = api_path.encode() + hashlib.sha256(encoded).digest()
        signature = hmac.new(base64.b64decode(self.secret), message, hashlib.sha512)
        sig_digest = base64.b64encode(signature.digest())

        return sig_digest.decode()

    async def _request(self, uri: str, headers: dict = None, data: dict = None) -> dict:
        async with httpx.AsyncClient() as client:
            result = await client.post(uri, headers=headers, data=data)
            if result.status_code not in (200, 201, 202):
                raise KrakyApiError(result.status_code)
            # check for error
            if len(result.json()["error"]) > 0:
                raise KrakyApiError(result.json()["error"])
            return result.json()["result"]

    async def public_request(self, endpoint: str, data: dict = None) -> dict:
        uri = f"{self.base_url}/0/public/{endpoint}"
        return await self._request(uri, data=data)

    async def private_request(self, endpoint: str, data: dict = None) -> dict:
        if not data:
            data = {}
        data["nonce"] = int(time.time() * 1000)
        api_path = f"/0/private/{endpoint}"
        uri = f"{self.base_url}{api_path}"
        headers = {
            "API-Key": self.api_key,
            "API-Sign": self._sign_message(api_path, data),
        }
        return await self._request(uri, headers=headers, data=data)

    async def get_server_time(self) -> dict:
        """https://api.kraken.com/0/public/Time"""
        return await self.public_request(endpoint="Time")

    async def get_asset_info(
        self, info: str = None, aclass: str = None, asset: str = None
    ) -> dict:
        """https://api.kraken.com/0/public/Assets"""
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self.public_request(endpoint="Assets", data=data)

    async def get_tradable_asset_pairs(self, info: str = None, pair: str = None) -> dict:
        """https://api.kraken.com/0/public/AssetPairs"""
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self.public_request(endpoint="AssetPairs", data=data)

    async def get_ticker_information(self, pair: str = None) -> dict:
        """https://api.kraken.com/0/public/Ticker"""
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self.public_request(endpoint="Ticker", data=data)

    async def get_ohlc_data(self, pair: str, interval: int = None, since: str = None) -> dict:
        """https://api.kraken.com/0/public/OHLC"""
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self.public_request(endpoint="OHLC", data=data)

    async def get_order_book(self, pair: str, count: int = None) -> dict:
        """https://api.kraken.com/0/public/Depth"""
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self.public_request(endpoint="Depth", data=data)

    async def get_recent_trades(self, pair: str, since: str = None) -> dict:
        """https://api.kraken.com/0/public/Trades"""
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self.public_request(endpoint="Trades", data=data)

    async def get_recent_spread_data(self, pair: str, since: str = None) -> dict:
        """https://api.kraken.com/0/public/Spread"""
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self.public_request(endpoint="Spread", data=data)

    async def get_account_balance(self) -> dict:
        """https://api.kraken.com/0/private/Balance"""
        return await self.private_request(endpoint="Balance")

    async def get_trade_balance(self, aclass: str = None, asset: str = None) -> dict:
        """https://api.kraken.com/0/private/TradeBalance"""
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self.private_request(endpoint="TradeBalance", data=data)

    async def get_open_orders(self, trades: bool = None, userref: str = None) -> dict:
        """https://api.kraken.com/0/private/OpenOrders"""
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self.private_request(endpoint="OpenOrders", data=data)

    async def get_closed_orders(
        self,
        trades: bool = None,
        userref: str = None,
        start: str = None,
        end: str = None,
        ofs: str = None,
        closetime: str = None,
    ) -> dict:
        """https://api.kraken.com/0/private/ClosedOrders"""
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self.private_request(endpoint="ClosedOrders", data=data)

    async def query_orders_info(
        self, txid: str, trades: bool = None, userref: str = None
    ) -> dict:
        """https://api.kraken.com/0/private/QueryOrders"""
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self.private_request(endpoint="TradesHistory", data=data)

    async def get_trades_history(
        self,
        type: str = None,
        trades: bool = None,
        start: str = None,
        end: str = None,
        ofs: str = None,
    ) -> dict:
        """https://api.kraken.com/0/private/TradesHistory"""
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self.private_request(endpoint="TradesHistory", data=data)

    async def query_trades_info(self, txid: str, trades: bool = None) -> dict:
        """https://api.kraken.com/0/private/QueryTrades"""
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self.private_request(endpoint="QueryTrades", data=data)

    async def get_open_positions(
        self, txid: str, docalcs: bool = None, consolidation: str = None
    ) -> dict:
        """https://api.kraken.com/0/private/OpenPositions"""
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self.private_request(endpoint="OpenPositions", data=data)

    async def get_ledgers_info(
        self,
        aclass: str = None,
        asset: str = None,
        type: str = None,
        start: str = None,
        end: str = None,
        ofs: str = None,
    ) -> dict:
        """https://api.kraken.com/0/private/Ledgers"""
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self.private_request(endpoint="Ledgers", data=data)

    async def query_ledgers(self, id: str) -> dict:
        """https://api.kraken.com/0/private/QueryLedgers"""
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self.private_request(endpoint="QueryLedgers", data=data)

    async def get_trade_volume(self, pair: str = None, fee_info: bool = None) -> dict:
        """https://api.kraken.com/0/private/TradeVolume"""
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self.private_request(endpoint="TradeVolume", data=data)

    async def request_export_report(
        self,
        description: str,
        report: str,
        format: str = None,
        fields: str = None,
        asset: str = None,
        starttm: str = None,
        endtm: str = None,
    ) -> dict:
        """https://api.kraken.com/0/private/AddExport"""
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self.private_request(endpoint="AddExport", data=data)

    async def add_standard_order(
        self,
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
    ) -> dict:
        """https://www.kraken.com/features/api#add-standard-order"""
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self.private_request(endpoint="AddOrder", data=data)

    async def cancel_open_order(self, txid: str) -> dict:
        """https://api.kraken.com/0/private/CancelOrder"""
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self.private_request(endpoint="CancelOrder", data=data)

    async def get_last_price(self, pair: str) -> float:
        ohlc = await self.get_ohlc_data(pair)
        return float(list(ohlc.values())[0][-1][4])

    async def get_web_sockets_token(self) -> str:
        """https://www.kraken.com/features/api#ws-auth"""
        result = await self.private_request(endpoint="GetWebSocketsToken")
        return result["token"]
