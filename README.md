# Kraky
Python asyncio client for Kraken API REST and Kraken Websockets API using httpx and websockets

## Installation 
    pip install kraky

## Docs

    https://kraky.readthedocs.io/en/latest/

## Usage

### REST

    from kraky import KrakyApiClient

    async def get_web_sockets_token():
        kraken_api_key = ""
        kraken_secret = ""
        kraky_api_client = KrakyApiClient(
            api_key=kraken_api_key, secret=kraken_secret
        )

        ws_token = await self.kraky_api_client.get_web_sockets_token()
        return ws_token

### Websocket

    from kraky import KrakyApiClient, KrakyWsClient

    async def get_ws_token():
        kraken_api_key = ""
        kraken_secret = ""
        kraky_api_client = KrakyApiClient(
            api_key=kraken_api_key, secret=kraken_secret
        )

        ws_token = await self.kraky_api_client.get_web_sockets_token()
        return ws_token

    async def public_handler(self, response):
        print(response)
    
    async def private_handler(self, response):
        print(response)

    async def main():

        interval = 30

        ws_pairs = ["XBT/USD", "ETH/USD]

        ws_token = get_token()

        kraky_public_ws_client = KrakyWsClient("production")
        kraky_private_ws_client = KrakyWsClient("production-auth")

        asyncio.create_task(
            kraky_public_ws_client.connect(
                public_handler, connection_name="public"
            )
        )

        asyncio.create_task(
            kraky_private_ws_client.connect(
                private_handler, connection_name="private"
            )
        )

        await kraky_public_ws_client.subscribe(
            {"name": "ohlc", "interval": interval},
            ws_pairs,
            connection_name="public",
        )

        await kraky_private_ws_client.subscribe(
            {
                "interval": interval,
                "token": ws_token,
                "name": "openOrders",
            },
            connection_name="private",
        )

    if __name__ == "__main__":
        loop = asyncio.get_event_loop()
        loop.create_task(main())
        loop.run_forever()

## Compatibility

- Python 3.7 and above

## Licence

MIT License