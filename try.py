import requests

def get_btc_price() -> float:
    """Fetch the live BTC price from Binance Options API."""
    resp = requests.get("https://eapi.binance.com/eapi/v1/index?underlying=BTCUSDT")
    resp.raise_for_status()
    return float(resp.json()["indexPrice"])

# Example usage
print(get_btc_price())
