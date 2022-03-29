from kraky import KrakyApiClient


kraky_api_client = KrakyApiClient()


class TestKrakyApiClient:
    def test_get_last_price(self):
        result = kraky_api_client.get_last_price("xbtusd")
        assert isinstance(result, float)

    def test_get_ohlc_data(self):
        result = kraky_api_client.get_ohlc_data("xbtusd", 1)
        assert "last" in result

    def test_get_tradable_asset_pairs(self):
        result = kraky_api_client.get_tradable_asset_pairs(pair="xbtusd")
        assert "XXBTZUSD" in result
