"""Kraky API module for Kraken's API implementation"""
import base64
import hashlib
import hmac
import urllib
import time

import httpx
from typing import Any

from .log import get_module_logger


class KrakyApiError(Exception):
    """Raise an exception when Kraken's API raise an error"""


class KrakyApi:
    def __init__(self, api_key: str = "", secret: str = "", tfa: bool = False) -> None:
        """
        Generate first an API key pair : https://support.kraken.com/hc/en-us/articles/360000919966-How-to-generate-an-API-key-pair-

        Arguments:
            api_key: The API key.
            secret: The Private key.
            tfa: Handle or not two-factor authentication (2FA)
        """
        self.base_url: str = "https://api.kraken.com"
        self.api_key = api_key
        self.secret = secret
        self.tfa = tfa
        self.otp: str = ""
        self.logger = get_module_logger(__name__)

    def _sign_message(self, api_path: str, data: dict) -> str:
        post_data = urllib.parse.urlencode(data)
        encoded = (str(data["nonce"]) + post_data).encode()
        message = api_path.encode() + hashlib.sha256(encoded).digest()
        signature = hmac.new(base64.b64decode(self.secret), message, hashlib.sha512)
        sig_digest = base64.b64encode(signature.digest())

        return sig_digest.decode()

    def set_otp(self, otp: str) -> None:
        """
        Set a OTP for private requests. Must be called each time you want to make a private request.

        Arguments:
            otp: two-factor password (two-factor must be enabled)
        """
        self.otp = otp


class KrakyApiAsyncClient(KrakyApi):
    """Kraken API AsyncClient implementation"""

    async def _request(self, uri: str, headers: dict = None, data: dict = None) -> dict:
        async with httpx.AsyncClient() as client:
            result = await client.post(uri, headers=headers, data=data)
            if result.status_code not in (200, 201, 202):
                raise KrakyApiError(result.status_code)
            # check for error
            if len(result.json()["error"]) > 0:
                raise KrakyApiError(result.json()["error"])
            return result.json()["result"]

    async def _public_request(self, endpoint: str, data: dict = None) -> Any:
        uri = f"{self.base_url}/0/public/{endpoint}"
        return await self._request(uri, data=data)

    async def _private_request(self, endpoint: str, data: dict = None) -> Any:
        if not data:
            data = {}
        data["nonce"] = int(time.time() * 1000)
        if self.tfa:
            data["otp"] = self.otp
        api_path = f"/0/private/{endpoint}"
        uri = f"{self.base_url}{api_path}"
        headers = {
            "API-Key": self.api_key,
            "API-Sign": self._sign_message(api_path, data),
        }
        return await self._request(uri, headers=headers, data=data)

    async def get_server_time(self, *args, **kwargs) -> dict:
        """
        https://docs.kraken.com/rest/#operation/getServerTime

        Return:
            Server's time

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        return await self._public_request(endpoint="Time")

    async def get_system_status(self, *args, **kwargs) -> dict:
        """
        https://docs.kraken.com/rest/#operation/getSystemStatus

        Return:
            System's status

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        return await self._public_request(endpoint="SystemStatus")

    async def get_asset_info(
        self, asset: str = None, aclass: str = None, *args, **kwargs
    ) -> dict:
        """
        https://docs.kraken.com/rest/#operation/getAssetInfo

        Arguments:
            asset: Comma delimited list of assets to get info on.
            aclass: Asset class. (optional, default: currency)

        Example:
            asset=XBT,ETH
            aclass=currency

        Return:
            Asset Info

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self._public_request(endpoint="Assets", data=data)

    async def get_tradable_asset_pairs(
        self, pair: str = None, info: str = None, *args, **kwargs
    ) -> dict:
        """
        https://docs.kraken.com/rest/#operation/getTradableAssetPairs

        Arguments:
            pair: Asset pairs to get data for
            info: Info to retrieve. (optional)

        Example:
            pair=XXBTCZUSD,XETHXXBT

        Return:
            Array of pair names and their info

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self._public_request(endpoint="AssetPairs", data=data)

    async def get_ticker_information(self, pair: str, *args, **kwargs) -> dict:
        """
        https://docs.kraken.com/rest/#operation/getTickerInformation

        Arguments:
            pair: Asset pair to get data for

        Example:
            pair=XBTUSD

        Return:
            Asset Ticker Info

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self._public_request(endpoint="Ticker", data=data)

    async def get_ohlc_data(
        self, pair: str, interval: int = None, since: str = None, *args, **kwargs
    ) -> dict:
        """
        https://docs.kraken.com/rest/#operation/getOHLCData

        Arguments:
            pair: Asset pair to get data for
            interval: Time frame interval in minutes
            since: Return committed OHLC data since given ID

        Example:
            pair=XBTUSD
            interval=60
            since=1548111600

        Return:
            Array of pair name and OHLC data

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self._public_request(endpoint="OHLC", data=data)

    async def get_order_book(
        self, pair: str, count: int = None, *args, **kwargs
    ) -> dict:
        """
        https://docs.kraken.com/rest/#operation/getOrderBook

        Arguments:
            pair: Asset pair to get data for
            count: maximum number of asks/bids

        Example:
            pair=XBTUSD
            count=2

        Return:
            Array of pair name and market depth

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self._public_request(endpoint="Depth", data=data)

    async def get_recent_trades(
        self, pair: str, since: str = None, *args, **kwargs
    ) -> dict:
        """
        https://docs.kraken.com/rest/#operation/getRecentTrades

        Arguments:
            pair: Asset pair to get data for
            since: Return trade data since given timestamp

        Example:
            pair=XBTUSD
            since=1616663618

        Return:
            Array of pair name and recent trade data

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self._public_request(endpoint="Trades", data=data)

    async def get_recent_spread_data(
        self, pair: str, since: str = None, *args, **kwargs
    ) -> dict:
        """
        https://www.kraken.com/features/api#get-recent-spread-data

        Arguments:
            pair: Asset pair to get data for
            since: Return spread data since given ID

        Example:
            pair=XBTUSD
            since=1548122302

        Return:
            Array of pair name and recent spread data

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self._public_request(endpoint="Spread", data=data)

    async def get_account_balance(self, *args, **kwargs) -> dict:
        """
        https://docs.kraken.com/rest/#operation/getAccountBalance

        Return:
            Account Balance

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        return await self._private_request(endpoint="Balance")

    async def get_trade_balance(
        self, aclass: str = None, asset: str = None, *args, **kwargs
    ) -> dict:
        """
        https://www.kraken.com/features/api#get-trade-balance

        Arguments:
            aclass: asset class (optional): currency (default)
            asset: base asset used to determine balance (default = ZUSD)

        Return:
            Array of trade balance info

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self._private_request(endpoint="TradeBalance", data=data)

    async def get_open_orders(
        self, trades: bool = False, userref: str = None, *args, **kwargs
    ) -> dict:
        """
        https://www.kraken.com/features/api#get-open-orders

        Arguments:
            trades: whether or not to include trades in output (optional.  default = false)
            userref: restrict results to given user reference id (optional)

        Return:
            Array of order info in open array with txid as the key

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self._private_request(endpoint="OpenOrders", data=data)

    async def get_closed_orders(
        self,
        trades: bool = False,
        userref: str = None,
        start: str = None,
        end: str = None,
        ofs: str = None,
        closetime: str = None,
        *args,
        **kwargs,
    ) -> dict:
        """
        https://www.kraken.com/features/api#get-closed-orders

        Arguments:
            trades: whether or not to include trades in output (optional.  default = false)
            userref: restrict results to given user reference id (optional)
            start: starting unix timestamp or order tx id of results (optional.  exclusive)
            end: ending unix timestamp or order tx id of results (optional.  inclusive)
            ofs: result offset
            closetime: which time to use (optional) open close both (default)

        Return: Array of order info

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self._private_request(endpoint="ClosedOrders", data=data)

    async def query_orders_info(
        self, txid: str, trades: bool = False, userref: str = None, *args, **kwargs
    ) -> dict:
        """
        https://www.kraken.com/features/api#query-orders-info

        Arguments:
            txid: comma delimited list of transaction ids to query info about (50 maximum)
            trades: whether or not to include trades in output (optional.  default = false)
            userref: restrict results to given user reference id (optional)

        Return:
            Associative array of orders info

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self._private_request(endpoint="TradesHistory", data=data)

    async def get_trades_history(
        self,
        type: str = None,
        trades: bool = False,
        start: str = None,
        end: str = None,
        ofs: str = None,
        *args, **kwargs
    ) -> dict:
        """
        https://www.kraken.com/features/api#get-trades-history

        Arguments:
            type: type of trade (optional)
            trades: whether or not to include trades related to position in output (optional.  default = false)
            start: starting unix timestamp or trade tx id of results (optional.  exclusive)
            end: ending unix timestamp or trade tx id of results (optional.  inclusive)
            ofs: result offset

        Return:
            Array of trade info

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self._private_request(endpoint="TradesHistory", data=data)

    async def query_trades_info(self, txid: str, trades: bool = False, *args, **kwargs) -> dict:
        """
        https://www.kraken.com/features/api#query-trades-info

        Arguments:
            txid: comma delimited list of transaction ids to query info about (20 maximum)
            trades: whether or not to include trades related to position in output (optional.  default = false)

        Return:
            Associative array of trades info

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self._private_request(endpoint="QueryTrades", data=data)

    async def get_open_positions(
        self, txid: str, docalcs: bool = False, consolidation: str = None, *args, **kwargs
    ) -> dict:
        """
        https://www.kraken.com/features/api#get-open-positions

        Arguments:
            txid: comma delimited list of transaction ids to restrict output to
            docalcs: whether or not to include profit/loss calculations (optional.  default = false)
            consolidation: what to consolidate the positions data around (optional.)

        Return:
            Associative array of open position info

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self._private_request(endpoint="OpenPositions", data=data)

    async def get_ledgers_info(
        self,
        aclass: str = None,
        asset: str = None,
        type: str = None,
        start: str = None,
        end: str = None,
        ofs: str = None,
        *args, **kwargs
    ) -> dict:
        """
        https://www.kraken.com/features/api#get-ledgers-info

        Arguments:
            aclass: asset class (optional): currency (default)
            asset: comma delimited list of assets to restrict output to (optional.  default = all)
            type: type of ledger to retrieve (optional)
            start: starting unix timestamp or ledger id of results (optional.  exclusive)
            end: ending unix timestamp or ledger id of results (optional.  inclusive)
            ofs: result offset

        Return:
            Associative array of ledgers info

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self._private_request(endpoint="Ledgers", data=data)

    async def query_ledgers(self, id: str, *args, **kwargs) -> dict:
        """
        https://www.kraken.com/features/api#query-ledgers

        Arguments:
            id: comma delimited list of ledger ids to query info about (20 maximum)

        Return:
            Associative array of ledgers info

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self._private_request(endpoint="QueryLedgers", data=data)

    async def get_trade_volume(self, pair: str = None, fee_info: bool = None, *args, **kwargs) -> dict:
        """
        https://www.kraken.com/features/api#get-trade-volume

        Arguments:
            pair: comma delimited list of asset pairs to get fee info on (optional)
            fee_info: whether or not to include fee info in results (optional)

        Return:
            Associative array

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self._private_request(endpoint="TradeVolume", data=data)

    async def request_export_report(
        self,
        description: str,
        report: str,
        format: str = None,
        fields: str = None,
        asset: str = None,
        starttm: str = None,
        endtm: str = None,
        *args, **kwargs
    ) -> str:
        """
        https://www.kraken.com/features/api#add-history-export

        Arguments:
            description: report description info
            report: report type (trades/ledgers)
            format: (CSV/TSV) (optional.  default = CSV)
            fields: comma delimited list of fields to include in report (optional.  default = all)
            asset: comma delimited list of assets to restrict output to (optional.  default = all)
            starttm: report start time (optional.  default = one year before now)
            endtm: report end time (optional.  default = now)

        Return:
            id: report id

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self._private_request(endpoint="AddExport", data=data)

    async def get_export_statuses(self, report: str, *args, **kwargs) -> dict:
        """
        https://www.kraken.com/features/api#add-history-export

        Arguments:
            report: report type (trades/ledgers)

        Return:
            id: report id

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self._private_request(endpoint="ExportStatus", data=data)

    async def get_export_report(self, id: str, *args, **kwargs) -> Any:
        """
        https://www.kraken.com/features/api#get-history-export
        Arguments:
            id: report id

        Return:
            Binary zip archive containing the report

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self._private_request(endpoint="RetrieveExport", data=data)

    async def remove_export_report(self, type: str, id: str, *args, **kwargs) -> str:
        """
        https://www.kraken.com/features/api#remove-history-export

        Arguments:
            type: remove type (cancel/delete)
            id: report id

        Return:
            Result of call

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self._private_request(endpoint="RemoveExport", data=data)

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
        *args, **kwargs
    ) -> dict:
        """
        https://www.kraken.com/features/api#add-standard-order

        Arguments:
            pair: asset pair
            type: type of order (buy/sell)
            ordertype: order type
            price: price (optional.  dependent upon ordertype)
            price2: secondary price (optional.  dependent upon ordertype)
            volume: order volume in lots
            leverage: amount of leverage desired (optional.  default = none)
            oflags: comma delimited list of order flags (optional)
            starttm: scheduled start time (optional)
            expiretm: expiration time (optional)
            userref: user reference id.  32-bit signed number.  (optional)
            validate: validate inputs only.  do not submit order (optional)
            close_ordertype: order type
            close_price: price
            close_price2: secondary price

        Return:
            descr: order description info
            txid: array of transaction ids for order (if order was added successfully)

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self._private_request(endpoint="AddOrder", data=data)

    async def cancel_open_order(self, txid: str, *args, **kwargs) -> dict:
        """
        https://www.kraken.com/features/api#cancel-open-order

        Arguments:
            txid: transaction id

        Return:
            count: number of orders canceled
            pending: if set, order(s) is/are pending cancellation

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self._private_request(endpoint="CancelOrder", data=data)

    async def cancel_all_open_orders(self, *args, **kwargs) -> dict:
        """
        https://www.kraken.com/features/api#cancel-all-open-orders

        Return:
            count: number of orders canceled

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return await self._private_request(endpoint="CancelAll", data=data)

    async def get_last_price(self, pair: str, *args, **kwargs) -> float:
        """
        Get last price for given pair

        Arguments:
            pair: currency to get last price

        Return:
            Last price in float

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        ohlc = await self.get_ohlc_data(pair)
        return float(list(ohlc.values())[0][-1][4])

    async def get_web_sockets_token(self, *args, **kwargs) -> str:
        """
        https://www.kraken.com/features/api#ws-auth

        Return:
            WS token

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        result = await self._private_request(endpoint="GetWebSocketsToken")
        return result["token"]


class KrakyApiClient(KrakyApi):
    def _request(self, uri: str, headers: dict = None, data: dict = None) -> dict:
        with httpx.Client() as client:
            result = client.post(uri, headers=headers, data=data)
            if result.status_code not in (200, 201, 202):
                raise KrakyApiError(result.status_code)
            # check for error
            if len(result.json()["error"]) > 0:
                raise KrakyApiError(result.json()["error"])
            return result.json()["result"]

    def _public_request(self, endpoint: str, data: dict = None) -> Any:
        uri = f"{self.base_url}/0/public/{endpoint}"
        return self._request(uri, data=data)

    def _private_request(self, endpoint: str, data: dict = None) -> Any:
        if not data:
            data = {}
        data["nonce"] = int(time.time() * 1000)
        if self.tfa:
            data["otp"] = self.otp
        api_path = f"/0/private/{endpoint}"
        uri = f"{self.base_url}{api_path}"
        headers = {
            "API-Key": self.api_key,
            "API-Sign": self._sign_message(api_path, data),
        }
        return self._request(uri, headers=headers, data=data)

    def get_server_time(self, *args, **kwargs) -> dict:
        """
        https://docs.kraken.com/rest/#operation/getServerTime

        Return:
            Server's time

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        return self._public_request(endpoint="Time")

    def get_system_status(self, *args, **kwargs) -> dict:
        """
        https://docs.kraken.com/rest/#operation/getSystemStatus

        Return:
            System's status

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        return self._public_request(endpoint="SystemStatus")

    def get_asset_info(
        self, asset: str = None, aclass: str = None, *args, **kwargs
    ) -> dict:
        """
        https://docs.kraken.com/rest/#operation/getAssetInfo

        Arguments:
            asset: Comma delimited list of assets to get info on.
            aclass: Asset class. (optional, default: currency)

        Example:
            asset=XBT,ETH
            aclass=currency

        Return:
            Asset Info

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return self._public_request(endpoint="Assets", data=data)

    def get_tradable_asset_pairs(
        self, pair: str = None, info: str = None, *args, **kwargs
    ) -> dict:
        """
        https://docs.kraken.com/rest/#operation/getTradableAssetPairs

        Arguments:
            pair: Asset pairs to get data for
            info: Info to retrieve. (optional)

        Example:
            pair=XXBTCZUSD,XETHXXBT

        Return:
            Array of pair names and their info

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return self._public_request(endpoint="AssetPairs", data=data)

    def get_ticker_information(self, pair: str, *args, **kwargs) -> dict:
        """
        https://docs.kraken.com/rest/#operation/getTickerInformation

        Arguments:
            pair: Asset pair to get data for

        Example:
            pair=XBTUSD

        Return:
            Asset Ticker Info

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return self._public_request(endpoint="Ticker", data=data)

    def get_ohlc_data(
        self, pair: str, interval: int = None, since: str = None, *args, **kwargs
    ) -> dict:
        """
        https://docs.kraken.com/rest/#operation/getOHLCData

        Arguments:
            pair: Asset pair to get data for
            interval: Time frame interval in minutes
            since: Return committed OHLC data since given ID

        Example:
            pair=XBTUSD
            interval=60
            since=1548111600

        Return:
            Array of pair name and OHLC data

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return self._public_request(endpoint="OHLC", data=data)

    def get_order_book(
        self, pair: str, count: int = None, *args, **kwargs
    ) -> dict:
        """
        https://docs.kraken.com/rest/#operation/getOrderBook

        Arguments:
            pair: Asset pair to get data for
            count: maximum number of asks/bids

        Example:
            pair=XBTUSD
            count=2

        Return:
            Array of pair name and market depth

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return self._public_request(endpoint="Depth", data=data)

    def get_recent_trades(
        self, pair: str, since: str = None, *args, **kwargs
    ) -> dict:
        """
        https://docs.kraken.com/rest/#operation/getRecentTrades

        Arguments:
            pair: Asset pair to get data for
            since: Return trade data since given timestamp

        Example:
            pair=XBTUSD
            since=1616663618

        Return:
            Array of pair name and recent trade data

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return self._public_request(endpoint="Trades", data=data)

    def get_recent_spread_data(
        self, pair: str, since: str = None, *args, **kwargs
    ) -> dict:
        """
        https://www.kraken.com/features/api#get-recent-spread-data

        Arguments:
            pair: Asset pair to get data for
            since: Return spread data since given ID

        Example:
            pair=XBTUSD
            since=1548122302

        Return:
            Array of pair name and recent spread data

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return self._public_request(endpoint="Spread", data=data)

    def get_account_balance(self, *args, **kwargs) -> dict:
        """
        https://docs.kraken.com/rest/#operation/getAccountBalance

        Return:
            Account Balance

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        return self._private_request(endpoint="Balance")

    def get_trade_balance(
        self, aclass: str = None, asset: str = None, *args, **kwargs
    ) -> dict:
        """
        https://www.kraken.com/features/api#get-trade-balance

        Arguments:
            aclass: asset class (optional): currency (default)
            asset: base asset used to determine balance (default = ZUSD)

        Return:
            Array of trade balance info

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return self._private_request(endpoint="TradeBalance", data=data)

    def get_open_orders(
        self, trades: bool = False, userref: str = None, *args, **kwargs
    ) -> dict:
        """
        https://www.kraken.com/features/api#get-open-orders

        Arguments:
            trades: whether or not to include trades in output (optional.  default = false)
            userref: restrict results to given user reference id (optional)

        Return:
            Array of order info in open array with txid as the key

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return self._private_request(endpoint="OpenOrders", data=data)

    def get_closed_orders(
        self,
        trades: bool = False,
        userref: str = None,
        start: str = None,
        end: str = None,
        ofs: str = None,
        closetime: str = None,
        *args,
        **kwargs,
    ) -> dict:
        """
        https://www.kraken.com/features/api#get-closed-orders

        Arguments:
            trades: whether or not to include trades in output (optional.  default = false)
            userref: restrict results to given user reference id (optional)
            start: starting unix timestamp or order tx id of results (optional.  exclusive)
            end: ending unix timestamp or order tx id of results (optional.  inclusive)
            ofs: result offset
            closetime: which time to use (optional) open close both (default)

        Return: Array of order info

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return self._private_request(endpoint="ClosedOrders", data=data)

    def query_orders_info(
        self, txid: str, trades: bool = False, userref: str = None, *args, **kwargs
    ) -> dict:
        """
        https://www.kraken.com/features/api#query-orders-info

        Arguments:
            txid: comma delimited list of transaction ids to query info about (50 maximum)
            trades: whether or not to include trades in output (optional.  default = false)
            userref: restrict results to given user reference id (optional)

        Return:
            Associative array of orders info

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return self._private_request(endpoint="TradesHistory", data=data)

    def get_trades_history(
        self,
        type: str = None,
        trades: bool = False,
        start: str = None,
        end: str = None,
        ofs: str = None,
        *args, **kwargs
    ) -> dict:
        """
        https://www.kraken.com/features/api#get-trades-history

        Arguments:
            type: type of trade (optional)
            trades: whether or not to include trades related to position in output (optional.  default = false)
            start: starting unix timestamp or trade tx id of results (optional.  exclusive)
            end: ending unix timestamp or trade tx id of results (optional.  inclusive)
            ofs: result offset

        Return:
            Array of trade info

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return self._private_request(endpoint="TradesHistory", data=data)

    def query_trades_info(self, txid: str, trades: bool = False, *args, **kwargs) -> dict:
        """
        https://www.kraken.com/features/api#query-trades-info

        Arguments:
            txid: comma delimited list of transaction ids to query info about (20 maximum)
            trades: whether or not to include trades related to position in output (optional.  default = false)

        Return:
            Associative array of trades info

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return self._private_request(endpoint="QueryTrades", data=data)

    def get_open_positions(
        self, txid: str, docalcs: bool = False, consolidation: str = None, *args, **kwargs
    ) -> dict:
        """
        https://www.kraken.com/features/api#get-open-positions

        Arguments:
            txid: comma delimited list of transaction ids to restrict output to
            docalcs: whether or not to include profit/loss calculations (optional.  default = false)
            consolidation: what to consolidate the positions data around (optional.)

        Return:
            Associative array of open position info

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return self._private_request(endpoint="OpenPositions", data=data)

    def get_ledgers_info(
        self,
        aclass: str = None,
        asset: str = None,
        type: str = None,
        start: str = None,
        end: str = None,
        ofs: str = None,
        *args, **kwargs
    ) -> dict:
        """
        https://www.kraken.com/features/api#get-ledgers-info

        Arguments:
            aclass: asset class (optional): currency (default)
            asset: comma delimited list of assets to restrict output to (optional.  default = all)
            type: type of ledger to retrieve (optional)
            start: starting unix timestamp or ledger id of results (optional.  exclusive)
            end: ending unix timestamp or ledger id of results (optional.  inclusive)
            ofs: result offset

        Return:
            Associative array of ledgers info

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return self._private_request(endpoint="Ledgers", data=data)

    def query_ledgers(self, id: str, *args, **kwargs) -> dict:
        """
        https://www.kraken.com/features/api#query-ledgers

        Arguments:
            id: comma delimited list of ledger ids to query info about (20 maximum)

        Return:
            Associative array of ledgers info

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return self._private_request(endpoint="QueryLedgers", data=data)

    def get_trade_volume(self, pair: str = None, fee_info: bool = None, *args, **kwargs) -> dict:
        """
        https://www.kraken.com/features/api#get-trade-volume

        Arguments:
            pair: comma delimited list of asset pairs to get fee info on (optional)
            fee_info: whether or not to include fee info in results (optional)

        Return:
            Associative array

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return self._private_request(endpoint="TradeVolume", data=data)

    def request_export_report(
        self,
        description: str,
        report: str,
        format: str = None,
        fields: str = None,
        asset: str = None,
        starttm: str = None,
        endtm: str = None,
        *args, **kwargs
    ) -> str:
        """
        https://www.kraken.com/features/api#add-history-export

        Arguments:
            description: report description info
            report: report type (trades/ledgers)
            format: (CSV/TSV) (optional.  default = CSV)
            fields: comma delimited list of fields to include in report (optional.  default = all)
            asset: comma delimited list of assets to restrict output to (optional.  default = all)
            starttm: report start time (optional.  default = one year before now)
            endtm: report end time (optional.  default = now)

        Return:
            id: report id

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return self._private_request(endpoint="AddExport", data=data)

    def get_export_statuses(self, report: str, *args, **kwargs) -> dict:
        """
        https://www.kraken.com/features/api#add-history-export

        Arguments:
            report: report type (trades/ledgers)

        Return:
            id: report id

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return self._private_request(endpoint="ExportStatus", data=data)

    def get_export_report(self, id: str, *args, **kwargs) -> Any:
        """
        https://www.kraken.com/features/api#get-history-export
        Arguments:
            id: report id

        Return:
            Binary zip archive containing the report

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return self._private_request(endpoint="RetrieveExport", data=data)

    def remove_export_report(self, type: str, id: str, *args, **kwargs) -> str:
        """
        https://www.kraken.com/features/api#remove-history-export

        Arguments:
            type: remove type (cancel/delete)
            id: report id

        Return:
            Result of call

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return self._private_request(endpoint="RemoveExport", data=data)

    def add_standard_order(
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
        *args, **kwargs
    ) -> dict:
        """
        https://www.kraken.com/features/api#add-standard-order

        Arguments:
            pair: asset pair
            type: type of order (buy/sell)
            ordertype: order type
            price: price (optional.  dependent upon ordertype)
            price2: secondary price (optional.  dependent upon ordertype)
            volume: order volume in lots
            leverage: amount of leverage desired (optional.  default = none)
            oflags: comma delimited list of order flags (optional)
            starttm: scheduled start time (optional)
            expiretm: expiration time (optional)
            userref: user reference id.  32-bit signed number.  (optional)
            validate: validate inputs only.  do not submit order (optional)
            close_ordertype: order type
            close_price: price
            close_price2: secondary price

        Return:
            descr: order description info
            txid: array of transaction ids for order (if order was added successfully)

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return self._private_request(endpoint="AddOrder", data=data)

    def cancel_open_order(self, txid: str, *args, **kwargs) -> dict:
        """
        https://www.kraken.com/features/api#cancel-open-order

        Arguments:
            txid: transaction id

        Return:
            count: number of orders canceled
            pending: if set, order(s) is/are pending cancellation

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return self._private_request(endpoint="CancelOrder", data=data)

    def cancel_all_open_orders(self, *args, **kwargs) -> dict:
        """
        https://www.kraken.com/features/api#cancel-all-open-orders

        Return:
            count: number of orders canceled

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        data = {
            arg: value
            for arg, value in locals().items()
            if arg != "self" and value is not None
        }
        return self._private_request(endpoint="CancelAll", data=data)

    def get_last_price(self, pair: str, *args, **kwargs) -> float:
        """
        Get last price for given pair

        Arguments:
            pair: currency to get last price

        Return:
            Last price in float

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        ohlc = self.get_ohlc_data(pair)
        return float(list(ohlc.values())[0][-1][4])

    def get_web_sockets_token(self, *args, **kwargs) -> str:
        """
        https://www.kraken.com/features/api#ws-auth

        Return:
            WS token

        Raises:
            KrakyApiError: If the error key's value is not empty
        """
        result = self._private_request(endpoint="GetWebSocketsToken")
        return result["token"]
