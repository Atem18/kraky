import asyncio

from kraky.ws import KrakyWsClient


async def public_handler(message):
    print(message)


async def main():
    kraky_ws_client = KrakyWsClient()

    asyncio.create_task(
        kraky_ws_client.connect(
            handler=public_handler, connection_name="public"
        )
    )

    await kraky_ws_client.subscribe(
        subscription={"name": "ohlc", "interval": 15},
        pair=["XBT/USD"],
        connection_name="public",
    )

    while True:
        await kraky_ws_client.ping(connection_name="public")
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
