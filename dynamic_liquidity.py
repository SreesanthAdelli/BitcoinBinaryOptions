import time
import math
from clients import KalshiBaseClient, KalshiHttpClient

def get_best_prices(orderbook):
    """Returns the best (lowest) YES and NO prices from the order book."""
    yes_orders = orderbook["orderbook"].get("yes", [])
    no_orders = orderbook["orderbook"].get("no", [])

    best_yes = yes_orders[0][0] if yes_orders else None
    best_no = no_orders[0][0] if no_orders else None


    return best_yes, best_no

def get_net_position(client, ticker):
    """Returns the net position of YES - NO contracts for a specific ticker.""" 
    positions = client.GetPositions()

    if not positions or "event_positions" not in positions:
        return 0  

    for market in positions["market_positions"]:
        if market["ticker"] == ticker:
            return market["position"]  
    
    return 0  

def dynamic_liquidity_provision(client, ticker):
    while True:
        # Step 1: Check current position
        net_position = get_net_position(client, ticker)
        print(f"Current net position: {net_position}")

        # Step 2: Get market order book
        market = client.GetMarketOrderbook(ticker, 1)
        print(market)
        best_bid_yes, best_bid_no = get_best_prices(market)
        sum_prices = best_bid_yes + best_bid_no
        spread = 100 - sum_prices
        order_size = 1

        sleep = 30

        print("Spread:" + str(spread))
        if not market:
            print("Market data unavailable. Skipping iteration.")
            time.sleep(sleep)
            continue  

        if best_bid_yes is None or best_bid_no is None:
            print("No valid bid prices. Skipping iteration.")
            time.sleep(sleep)
            continue

        if spread < 5 and net_position == 0:
            print("Spread too tight. Skipping iteration.")
            time.sleep(sleep)
            continue


        premium = math.floor(spread/2) - 1

        # Step 3: Make trading decisions based on position
        if net_position == 0 and sum_prices < 97:
            print("Neutral position. Placing balanced orders.")
            client_order_id = f"order_{int(time.time())}"
            client.PostOrder(ticker=ticker, client_order_id=client_order_id, action="buy", type='limit', side='yes', yes_price=best_bid_yes + premium, count=order_size, expiration_ts=sleep)
            client_order_id = f"order_{int(time.time())}"
            client.PostOrder(ticker=ticker, client_order_id=client_order_id, action="buy", type='limit', side='no', no_price=best_bid_no + premium, count=order_size, expiration_ts=sleep)

        elif net_position > 0:
            print("More YES contracts than NO. Selling to balance.")
            client_order_id = f"order_{int(time.time())}"
            client.PostOrder(ticker=ticker, client_order_id=client_order_id, action="buy", type='limit', side='no', no_price=best_bid_no + premium, count=order_size, expiration_ts=sleep)

        elif net_position < 0:
            print("More NO contracts than YES. Buying to balance.")
            client_order_id = f"order_{int(time.time())}"
            client.PostOrder(ticker=ticker, client_order_id=client_order_id, action="buy", type='limit', side='yes', yes_price=best_bid_yes + premium, count=order_size, expiration_ts=sleep)

        # Step 4: Wait 5 seconds before restarting loop
        time.sleep(sleep)

