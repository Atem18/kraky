import typer

from kraky import KrakyApiClient


app = typer.Typer()


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def main(
    ctx: typer.Context,
    endpoint: str = typer.Argument(
        "get_system_status",
        envvar="KRAKY_ENDPOINT",
        help="Kraky function to call. See full list here : https://kraky.readthedocs.io/en/latest/api/",
    ),
    kraken_api_key: str = typer.Option(
        "",
        envvar="KRAKEN_API_KEY",
        help="See here to generate a pair : https://support.kraken.com/hc/en-us/articles/360000919966-How-to-generate-an-API-key-pair-"
    ),
    kraken_secret: str = typer.Option(
        "",
        envvar="KRAKEN_SECRET",
        help="See here to generate a pair : https://support.kraken.com/hc/en-us/articles/360000919966-How-to-generate-an-API-key-pair-"
    ),
    tfa: bool = typer.Option(
        False,
        envvar="KRAKY_TFA",
        help="Enable two-factor authentication. More info here : https://support.kraken.com/hc/en-us/articles/360000714526"
    ),
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
        result = getattr(kraky_api_client, endpoint)(*args, **kwargs)
        typer.echo(f"{result}")
    except TypeError as err:
        typer.echo(err)
    except AttributeError:
        typer.echo("Endpoint not supported!")
