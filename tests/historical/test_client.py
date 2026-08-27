from ibapi.common import BarData

from src.historical.client import HistoricalClient


def test_client_maps_installed_ibapi_bar_average_to_wap():
    bar = BarData()
    bar.date = "1787515200"
    bar.open = 6000
    bar.high = 6001
    bar.low = 5999
    bar.close = 6000
    bar.volume = 12
    bar.average = 6000
    bar.barCount = 3
    client = HistoricalClient()

    client.historicalData(10001, bar)

    assert client.response.bars[0].wap == 6000
    assert client.response.bars[0].bar_count == 3

