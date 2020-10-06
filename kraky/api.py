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
    def __init__(self, api_key="", secret=""):
        self.base_url = "https://api.kraken.com"
        self.api_key = api_key
        self.secret = secret
        self.logger = get_module_logger(__name__)

    async def _request(self, uri, headers=None, data=None):
        async with httpx.AsyncClient() as client:
            result = await client.post(uri, headers=headers, data=data)
            if result.status_code not in (200, 201, 202):
                self.logger.exception(result.raise_for_status())
            # check for error
            if len(result.json()["error"]) > 0:
                raise KrakyApiError(result.json()["error"])
            return result.json()["result"]

    async def public_request(self, endpoint, data=None):
        uri = f"{self.base_url}/0/public/{endpoint}"
        return await self._request(uri, data=data)

    async def private_request(self, endpoint, data=None):
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

    def _sign_message(self, api_path, data):
        post_data = urllib.parse.urlencode(data)
        encoded = (str(data["nonce"]) + post_data).encode()
        message = api_path.encode() + hashlib.sha256(encoded).digest()
        signature = hmac.new(base64.b64decode(self.secret), message, hashlib.sha512)
        sig_digest = base64.b64encode(signature.digest())

        return sig_digest.decode()

    async def add_order(self, data):
        return await self.private_request(endpoint="AddOrder", data=data)

    async def cancel_order(self, data):
        return await self.private_request(endpoint="CancelOrder", data=data)

    async def get_ws_token(self):
        """https://www.kraken.com/features/api#ws-auth"""
        result = await self.private_request(endpoint="GetWebSocketsToken")
        return result["token"]

    async def get_trade_balances(self):
        return await self.private_request(endpoint="Balance")

    async def get_open_positions(self):
        return await self.private_request(endpoint="OpenPositions")

    async def get_open_orders(self):
        return await self.private_request(endpoint="OpenOrders")

    async def cancel_open_order(self, txid):
        return await self.private_request(endpoint="CancelOrder", data={"txid": txid})

    async def get_trades_history(self, trade_type=None, trades=None, start=None, end=None, ofs=None):
        data = {"type": trade_type, "trades": trades, "start": start, "end": end, "ofs": ofs}
        return await self.private_request(endpoint="TradesHistory", data=data)

    async def get_recent_trades(self, pair: str, since=None):
        data = {"pair": pair, "since": since}
        return await self.public_request(endpoint="Trades", data=data)

    async def get_ohlc_data(self, pair: str, interval: int, since=None):
        data = {"pair": pair, "interval": interval, "since": since}
        return await self.public_request(endpoint="OHLC", data=data)

    async def get_asset_pairs(self, info=None, pair=None):
        data = {"info": info, "pair": pair}
        return await self.public_request(endpoint="AssetPairs", data=data)

    async def get_last_price(self, pair: str):
        ohlc = await self.get_ohlc_data(pair, interval=1)
        return float(list(ohlc.values())[0][-1][4])
