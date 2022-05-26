[![Total alerts](https://img.shields.io/lgtm/alerts/g/Atem18/kraky.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/Atem18/kraky/alerts/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/Atem18/kraky.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/Atem18/kraky/context:python)

# Kraky
Python client for Kraken API REST and Kraken Websockets API using httpx and websockets.
Supports both sync and async for API REST.

## Disclaimer
This software is for educational purposes only. Do not risk money which you are afraid to lose. USE THE SOFTWARE AT YOUR OWN RISK. THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR TRADING RESULTS.

Always start by running a trading bot in Dry-run and do not engage money before you understand how it works and what profit/loss you should expect.

We strongly recommend you to have coding and Python knowledge. Do not hesitate to read the source code and understand the mechanism of this library.

## Installation 
    pip install kraky

## Docs

    https://kraky.readthedocs.io/en/latest/

## Usage

### CLI

Kraky provides a CLI that matches the API function names and args.

You can use it like the following:

```bash
kraky get_ohlc_data pair=XBTUSD interval=240
```

You can replace get_ohlc_data by any kraky API function and pair=XBTUSD or interval=240 by any function argument.
Please respect the format key=value.

It also supports .env files so you can also create a .env file with your api_key and secret and kraky will pick them up.

Example:
```bash
KRAKEN_API_KEY=""
KRAKEN_SECRET=""
```

### Sync REST API
```python
from kraky import KrakyApiClient


def get_web_sockets_token():
    kraken_api_key = ""
    kraken_secret = ""
    kraky_api_client = KrakyApiClient(
        api_key=kraken_api_key, secret=kraken_secret
    )

    ws_token = kraky_api_client.get_web_sockets_token()
    return ws_token

get_web_sockets_token()
```

### Async REST API
```python
from kraky import KrakyApiAsyncClient


async def get_web_sockets_token():
    kraken_api_key = ""
    kraken_secret = ""
    kraky_api_client = KrakyApiAsyncClient(
        api_key=kraken_api_key, secret=kraken_secret
    )

    ws_token = await kraky_api_client.get_web_sockets_token()
    return ws_token

asyncio.run(get_web_sockets_token)
```

### Websocket

```python
import asyncio
from kraky import KrakyApiAsyncClient, KrakyWsClient


async def get_web_sockets_token():
    kraken_api_key = ""
    kraken_secret = ""
    kraky_api_client = KrakyApiAsyncClient(
        api_key=kraken_api_key, secret=kraken_secret
    )

    ws_token = await kraky_api_client.get_web_sockets_token()
    return ws_token


async def public_handler(response):
    print(response)


async def private_handler(response):
    print(response)


async def main():

    interval = 30

    ws_pairs = ["XBT/USD", "ETH/USD"]

    ws_token = await get_web_sockets_token()

    kraky_public_ws_client = KrakyWsClient("production")
    kraky_private_ws_client = KrakyWsClient("production-auth")

    asyncio.create_task(
        kraky_public_ws_client.connect(public_handler, connection_name="public")
    )

    asyncio.create_task(
        kraky_private_ws_client.connect(private_handler, connection_name="private")
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

```

## Compatibility

- Python 3.7 and above

## Licence

MIT License
