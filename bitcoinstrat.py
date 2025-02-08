import numpy as np
import requests
import time
import math
from scipy.stats import norm
from clients import KalshiBaseClient, KalshiHttpClient
from datetime import datetime, timezone

def get_time_to_expiry(expiration_time):
    """
    Calculates the time to expiry in hours from a given expiration time string.

    Parameters:
    expiration_time (str): Expiration time in ISO 8601 format (e.g., '2025-02-15T05:00:00Z').

    Returns:
    float: Time to expiry in hours.
    """
    expiry_dt = datetime.strptime(expiration_time, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    now_dt = datetime.now(timezone.utc)
    time_to_expiry = (expiry_dt - now_dt).total_seconds() / 3600  # Convert seconds to hours
    return max(time_to_expiry, 0)  # Ensure non-negative value


def binary_option_price(S0, K, T_hours, IV_percent, r=0.0):
    """
    Compute the fair price of a binary option contract.

    Parameters:
    S0 (float): Current Bitcoin price.
    K (float): Strike price of the binary option.
    T_hours (float): Time to expiry in hours.
    IV_percent (float): Implied volatility in percentage (e.g., 50 for 50%).
    r (float): Risk-free rate (default is 0%).

    Returns:
    float: Fair price of the binary contract (probability of Bitcoin ≥ K at expiry).
    """
    # Convert time from hours to years
    T = T_hours / (24 * 365)

    # Convert IV from percentage to decimal
    sigma = IV_percent / 100

    # Compute d2
    d2 = (np.log(S0 / K) - (0.5 * sigma**2 * T)) / (sigma * np.sqrt(T))

    # Compute binary option price using N(d2)
    return norm.cdf(d2)

# Function to get live Bitcoin price from Binance
def get_bitcoin_price():
    url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
    response = requests.get(url)
    data = response.json()
    return float(data["price"])

def get_bitcoin_markets(client):
    """
    Filters and returns only Bitcoin-related markets from the full list of markets.
    
    Returns:
    list: A list of Bitcoin-related market dictionaries.
    """
    series_ticker = "KXBTCD"
    btc_markets = client.get_markets(series_ticker=series_ticker)  # Assumes you have a function named get_markets()

    return btc_markets



def bitcoinstrat(client, IV_percent, spread, refresh_rate):
    """
    Implements a market-making strategy for Bitcoin binary contracts on Kalshi.

    Parameters:
    client (KalshiHttpClient): The Kalshi client to interact with the exchange.
    IV_percent (float): Implied volatility in percentage (e.g., 50 for 50%).
    spread (float): Spread around the fair probability (default is 2%).
    refresh_rate (int): How often to refresh market data in seconds (default is 10s).
    """

    print("Starting Bitcoin market-making strategy...")
    
    while True:
        try:
            print("\nFetching live Bitcoin price...")
            btc_price = get_bitcoin_price()
            print(f"Current Bitcoin price: ${btc_price:.2f}")

            print("Fetching Bitcoin-related markets from Kalshi...")
            btc_markets = get_bitcoin_markets(client)
            print(f"Found {len(btc_markets)} Bitcoin markets.")

            for market in btc_markets:
                if market["volume_24h"] > 1000:
                    print(f"Skipping {market['ticker']} due to high 24h volume ({market['volume_24h']}).")
                    continue

                strike_price = float(market["floor_strike"])
                time_to_expiry = get_time_to_expiry(market["expiration_time"])
                print(f"\nProcessing market {market['ticker']} - Strike Price: {strike_price}, Time to Expiry: {time_to_expiry:.2f} hours")

                # Compute fair price
                fair_price = binary_option_price(btc_price, strike_price, time_to_expiry, IV_percent)
                print(f"Calculated fair probability: {fair_price:.4f}")


                # Determine bid and ask prices with spread
                bid_price = int(math.floor(max(0, (fair_price - spread / 2))* 100) / 100)
                ask_price = int(math.ceil(min(1, (fair_price + spread / 2))* 100) / 100)
                print(f"Placing orders - Bid: {bid_price:.4f}, Ask: {ask_price:.4f}")

                # Get current order book prices
                current_bid = market.get("yes_bid", 0)
                current_ask = market.get("no_bid", 1)
                order_size = 1
                # Market-making strategy: buy below fair price, sell above

                if fair_price > 0.9 or fair_price < 0.1:
                    continue
                if current_bid < bid_price:
                    client_order_id = f"order_{int(time.time())}"
                    print(f"Placing BUY order on {market['ticker']} at {bid_price:.4f}")
                    client.PostOrder(ticker=market['ticker'], client_order_id=client_order_id, action="buy", type='limit', side='yes', yes_price=bid_price*100, count=order_size, expiration_ts=refresh_rate)

                if current_ask > ask_price:
                    client_order_id = f"order_{int(time.time())}"
                    print(f"Placing SELL order on {market['ticker']} at {ask_price:.4f}")
                    client.PostOrder(ticker=market['ticker'], client_order_id=client_order_id, action="buy", type='limit', side='no', no_price=ask_price*100, count=order_size, expiration_ts=refresh_rate)

            print(f"Sleeping for {refresh_rate} seconds before next update...")
            time.sleep(refresh_rate)

        except Exception as e:
            print(f"Error in strategy execution: {e}")
            time.sleep(refresh_rate)