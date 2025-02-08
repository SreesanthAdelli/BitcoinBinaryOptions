import time
from datetime import datetime, timedelta
from clients import KalshiHttpClient  # Import necessary functions

def filter_markets(results, price_threshold=90, volume_threshold=100):
    """
    Filters markets where the price is greater than the given threshold
    and the 24-hour volume is above the specified threshold.
    Returns a list of (ticker, yes_ask_price) tuples for markets meeting the criteria.
    """
    return [
    (result['ticker'])
    for result in results
    if result['yes_ask'] >= price_threshold and result['volume_24h'] > volume_threshold
    ]

def fetch_all_markets(client, max_close_ts, min_close_ts, limit=1000):
    """
    Fetches all markets, paginating through results using the cursor.
    """
    all_results = []
    cursor = None
    x = 0

    while True:
        # Fetch results, passing the cursor for pagination
        response = client.get_markets(limit=limit, max_close_ts=max_close_ts, min_close_ts=min_close_ts, cursor=cursor)
        
        # Extract markets (assuming it's the top level of the response) and the cursor from the response
        markets = response[:-1]  
        cursor = response[-1]  # Extract cursor for pagination
        
        # Add the fetched results to the list
        all_results.extend(markets)
        
        # If there's no next cursor, break the loop
        if not cursor:
            break

    return all_results





def trade_ninetypercent(client):
    """
    Fetches markets, filters those where price > 0.9 and volume > 1000, and executes trades.
    """
    # Current time in seconds
    current_time = int(time.time())

    # 24 hours from current time in seconds
    closeby_time = current_time + (24 * 60 * 60)

    # Fetch and filter markets
    results = fetch_all_markets(client, max_close_ts=closeby_time, min_close_ts=current_time)
    print(len(results))
    filtered_markets = filter_markets(results)
    print(filtered_markets)

    # Execute trades
    for ticker in filtered_markets:
        # client_order_id = f"order_{int(time.time())}"
        client.PostOrder(
            action="buy",
            client_order_id=client_order_id,
            type="market",
            ticker=ticker,
            side="yes",
            count=1,  # Modify count as needed
        )

    print(f"Traded in markets: {[ticker for ticker, _ in filtered_markets]}")
