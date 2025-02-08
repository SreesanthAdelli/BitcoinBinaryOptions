from clients import KalshiBaseClient, KalshiHttpClient
from config import list_markets
import time

def get_best_prices(orderbook):
    """Returns the best (lowest) YES and NO prices from the order book."""
    yes_orders = orderbook["orderbook"]["yes"] if "yes" in orderbook["orderbook"] else []
    no_orders = orderbook["orderbook"]["no"] if "no" in orderbook["orderbook"] else []


    best_yes = yes_orders[0][0] if yes_orders else None
    best_no = no_orders[0][0] if no_orders else None

    return best_yes, best_no

def should_trade(orderbook):
    """Returns True if the sum of the best YES and NO prices is ≤ 95."""
    best_yes, best_no = get_best_prices(orderbook)
    
    if best_yes is None or best_no is None:
        return False  # Skip if order book is empty
    
    
    return (best_yes + best_no) <= 95


def trade_strategy(client):
    """Loops through markets and places trades when conditions are met."""
    cursor = "0"
    limit = 1000
    
    while cursor != None:
        if cursor != 0:
            markets = client.get_markets(cursor)
        else:
            markets = client.get_markets()
        for market in markets:  # Fetch active markets
            time.sleep(0.1)
            ticker = market['ticker']
            print(f"Checking market: {ticker}")
            depth = 1
            if int(market['volume']) > 1000:
                orderbook = client.GetMarketOrderbook(ticker, depth)
            else:
                continue
            print(orderbook)
            best_prices = get_best_prices(orderbook)
            print(best_prices)
            if should_trade(orderbook):
                print("Should Trade")
                best_yes, best_no = get_best_prices(orderbook)

                # Buy at the best price available
                client_order_id = f"order_{int(time.time())}"

                response = client.PostOrder(
                    action = 'buy',
                    client_order_id = client_order_id,
                    count = 1,
                    side = 'yes',
                    ticker = ticker,
                    type = 'limit',
                    yes_price = best_yes + 5
                )

                print("Yes Order Made")
                print(response)
                time.sleep(1)

                client_order_id = f"order_{int(time.time())}"

                response = client.PostLimitOrder(
                    action = 'buy',
                    client_order_id = client_order_id,
                    count = 1,
                    side = 'no',
                    ticker = ticker,
                    type = 'limit',
                    no_price = best_no + 5
                )

                print("No Order Made")
                print(response)
                time.sleep(1)


                balance = client.get_balance()
                print(balance)
                    


    return 0
