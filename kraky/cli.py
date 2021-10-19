import asyncio
import typer

from kraky import KrakyApiClient


app = typer.Typer()


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def main(
    ctx: typer.Context,
    endpoint: str,
    kraken_api_key: str = "",
    kraken_secret: str = "",
    tfa: bool = False
):
    kraky_api_client = KrakyApiClient(
        api_key=kraken_api_key, secret=kraken_secret, tfa=tfa
    )
    args: list = []
    kwargs: dict = {}
    for arg in ctx.args:
        kwarg = arg.split("=")
        kwargs[kwarg[0]] = kwarg[1]
    try:
        result = asyncio.run(getattr(kraky_api_client, endpoint)(*args, **kwargs))
        typer.echo(f"{result}")
    except TypeError as err:
        typer.echo(err)
    except AttributeError:
        typer.echo("Endpoint not supported!")
