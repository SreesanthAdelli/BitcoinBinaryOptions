import requests
import base64
import time
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid

from requests.exceptions import HTTPError

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature

import websockets

class Environment(Enum):
    DEMO = "demo"
    PROD = "prod"

class KalshiBaseClient:
    """Base client class for interacting with the Kalshi API."""
    def __init__(
        self,
        key_id: str,
        private_key: rsa.RSAPrivateKey,
        environment: Environment = Environment.DEMO,
    ):
        """Initializes the client with the provided API key and private key.

        Args:
            key_id (str): Your Kalshi API key ID.
            private_key (rsa.RSAPrivateKey): Your RSA private key.
            environment (Environment): The API environment to use (DEMO or PROD).
        """
        self.key_id = key_id
        self.private_key = private_key
        self.environment = environment
        self.last_api_call = datetime.now()

        if self.environment == Environment.DEMO:
            self.HTTP_BASE_URL = "https://demo-api.kalshi.co"
            self.WS_BASE_URL = "wss://demo-api.kalshi.co"
        elif self.environment == Environment.PROD:
            self.HTTP_BASE_URL = "https://api.elections.kalshi.com"
            self.WS_BASE_URL = "wss://api.elections.kalshi.com"
        else:
            raise ValueError("Invalid environment")

    def request_headers(self, method: str, path: str) -> Dict[str, Any]:
        """Generates the required authentication headers for API requests."""
        current_time_milliseconds = int(time.time() * 1000)
        timestamp_str = str(current_time_milliseconds)

        # Remove query params from path
        path_parts = path.split('?')

        msg_string = timestamp_str + method + path_parts[0]
        signature = self.sign_pss_text(msg_string)

        headers = {
            "Content-Type": "application/json",
            "KALSHI-ACCESS-KEY": self.key_id,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": timestamp_str,
        }
        return headers

    def sign_pss_text(self, text: str) -> str:
        """Signs the text using RSA-PSS and returns the base64 encoded signature."""
        message = text.encode('utf-8')
        try:
            signature = self.private_key.sign(
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return base64.b64encode(signature).decode('utf-8')
        except InvalidSignature as e:
            raise ValueError("RSA sign PSS failed") from e

class KalshiHttpClient(KalshiBaseClient):
    """Client for handling HTTP connections to the Kalshi API."""
    def __init__(
        self,
        key_id: str,
        private_key: rsa.RSAPrivateKey,
        environment: Environment = Environment.PROD,
    ):
        super().__init__(key_id, private_key, environment)
        self.host = self.HTTP_BASE_URL
        self.exchange_url = "/trade-api/v2/exchange"
        self.markets_url = "/trade-api/v2/markets"
        self.portfolio_url = "/trade-api/v2/portfolio"

    def rate_limit(self) -> None:
        """Built-in rate limiter to prevent exceeding API rate limits."""
        THRESHOLD_IN_MILLISECONDS = 100
        now = datetime.now()
        threshold_in_microseconds = 1000 * THRESHOLD_IN_MILLISECONDS
        threshold_in_seconds = THRESHOLD_IN_MILLISECONDS / 1000
        if now - self.last_api_call < timedelta(microseconds=threshold_in_microseconds):
            time.sleep(threshold_in_seconds)
        self.last_api_call = datetime.now()

    def raise_if_bad_response(self, response: requests.Response) -> None:
        """Raises an HTTPError if the response status code indicates an error."""
        if response.status_code not in range(200, 299):
            response.raise_for_status()

    def post(self, path: str, body: dict) -> Any:
        """Performs an authenticated POST request to the Kalshi API."""
        self.rate_limit()
        response = requests.post(
            self.host + path,
            json=body,
            headers=self.request_headers("POST", path)
        )
        self.raise_if_bad_response(response)
        return response.json()

    def get(self, path: str, params: Dict[str, Any] = {}) -> Any:
        """Performs an authenticated GET request to the Kalshi API."""
        self.rate_limit()
        response = requests.get(
            self.host + path,
            headers=self.request_headers("GET", path),
            params=params
        )
        self.raise_if_bad_response(response)
        return response.json()

    def delete(self, path: str, params: Dict[str, Any] = {}) -> Any:
        """Performs an authenticated DELETE request to the Kalshi API."""
        self.rate_limit()
        response = requests.delete(
            self.host + path,
            headers=self.request_headers("DELETE", path),
            params=params
        )
        self.raise_if_bad_response(response)
        return response.json()

    def get_balance(self) -> Dict[str, Any]:
        """Retrieves the account balance."""
        return self.get(self.portfolio_url + '/balance')

    def get_exchange_status(self) -> Dict[str, Any]:
        """Retrieves the exchange status."""
        return self.get(self.exchange_url + "/status")

    def get_trades(
        self,
        ticker: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        max_ts: Optional[int] = None,
        min_ts: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Retrieves trades based on provided filters."""
        params = {
            'ticker': ticker,
            'limit': limit,
            'cursor': cursor,
            'max_ts': max_ts,
            'min_ts': min_ts,
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        return self.get(self.markets_url + '/trades', params=params)
    def GetMarketOrderbook(
        self,
        ticker: str, 
        depth: Optional[int] = None
    ) -> Dict[str, Any]:
        # Retrives Orderbook for given market (ticker) at given depth
        url = f"{self.markets_url}/{ticker}/orderbook"
        if depth is not None:
            url += f"?depth={depth}"  # Append depth as a query parameter
        params = {
            'ticker': ticker
        }
        if depth is not None:
            params[depth] = depth
        return self.get(url, params=params)

    def get_markets(
            self,
            limit: Optional[int] = None,
            cursor: Optional[str] = None, 
            status: Optional[str] = None,
            series_ticker: Optional[str] = None,
            max_close_ts: Optional[int] = None,
            min_close_ts: Optional[int] = None
            ) -> Dict:
        """
        Fetches a list of markets from the Kalshi API.

        Parameters:
        - api_key (str): Your API key for authentication.
        - limit (int): The number of markets to return. Default is 100.
        - cursor (str, optional): Pagination cursor from previous requests to get the next set of markets.
        - status (str, optional): A comma-separated list of market statuses (e.g., "open", "unopened").

        Returns:
        - Dict: A dictionary containing market data.
        """

        headers = {"accept": "application/json"}
        

        params = {
            "limit": limit,
            "cursor": cursor,
            "status": status,
            "series_ticker": series_ticker,
            "max_close_ts": max_close_ts,
            "min_close_ts": min_close_ts
        }
        
        params = {k: v for k, v in params.items() if v is not None}

        url = f"https://api.elections.kalshi.com/trade-api/v2/markets"


        # Send the GET request to the API
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(response.url)
            raise Exception(f"Failed to fetch markets: {response.status_code} - {response.text}")
        
        # Parse the response JSON
        data = response.json()

        # Check if 'markets' key exists in the response
        if "markets" in data:
            return data["markets"]
        else:
            return {}



    def PostOrder(
        self,
        action: str,
        client_order_id: str,
        count: int,
        side: str,
        ticker: str,
        type: str,
        expiration_ts: Optional[int] = None,
        no_price: Optional[int] = None,
        yes_price: Optional[int] = None,
    ) -> dict:
        """
        Submits a limit order to the Kalshi API.

        Args:
            action (str): Specifies if this is a buy or sell order
            client_order_id (str): Unique identifier for the order.
            count (int): Number of contracts to be bought or sold.
            expiration_ts (Optional[int]): Expiration time of the order in UNIX seconds.
            no_price (Optional[int]): Price in cents for a 'No' order.
            yes_price (Optional[int]): Price in cents for a 'Yes' order.
            side (str): Specifies if this is a 'yes' or 'no' order.
            ticker (str): The ticker of the market the order will be placed in.
            type (str): Specifies if this is a "market" or a "limit" order.

        Returns:
            dict: Response from the Kalshi API.
        """
        url = "https://api.elections.kalshi.com/trade-api/v2/portfolio/orders"
        

        # Construct the payload
        payload = {
            "action": action,
            "client_order_id": client_order_id,
            "count": count,
            "side": side,
            "ticker": ticker,
            "type": type
        }

        if expiration_ts:
            payload["expiration_ts"] = expiration_ts

        if yes_price is not None:
            payload["yes_price"] = yes_price
        elif no_price is not None:
            payload["no_price"] = no_price
        # Generate the timestamp and signature for authentication
        timestamp_str = str(int(time.time() * 1000))  # Current time in milliseconds
        signature = self.sign_pss_text(timestamp_str + "POST" + "/trade-api/v2/portfolio/orders")

        # Set the headers
        headers = {
            "Content-Type": "application/json",
            "KALSHI-ACCESS-KEY": self.key_id,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": timestamp_str,
        }

        print(payload)
        response = requests.post(url, json=payload, headers=headers)

        # Check if the request was successful
        if response.status_code != 201:
            raise Exception(f"Order submission failed: {response.status_code}, {response.text}")

        return response.json()

    def GetPositions(
            self,
            cursor: Optional[str] = None,
            limit: Optional[str] = None,
            ticker: Optional[str] = None,
            count_filter: Optional[str] = None,
            settlement_status: Optional[str] = None,
            event_ticker: Optional[str] = None
    ) -> dict:
        url = 'https://api.elections.kalshi.com/trade-api/v2/portfolio/positions'
        
        headers = {"accept": "application/json"}

        params = {
        "cursor": cursor,
        "limit": limit,
        "count_filter": count_filter,
        "settlement_status": settlement_status,
        "ticker": ticker,
        "event_ticker": event_ticker
    }
    
        # Remove any parameters that are None
        params = {key: value for key, value in params.items() if value is not None}
    
        return self.get(self.portfolio_url + '/positions', params=params)

    
class KalshiWebSocketClient(KalshiBaseClient):
    """Client for handling WebSocket connections to the Kalshi API."""
    def __init__(
        self,
        key_id: str,
        private_key: rsa.RSAPrivateKey,
        environment: Environment = Environment.DEMO,
    ):
        super().__init__(key_id, private_key, environment)
        self.ws = None
        self.url_suffix = "/trade-api/ws/v2"
        self.message_id = 1  # Add counter for message IDs

    async def connect(self):
        """Establishes a WebSocket connection using authentication."""
        host = self.WS_BASE_URL + self.url_suffix
        auth_headers = self.request_headers("GET", self.url_suffix)
        async with websockets.connect(host, additional_headers=auth_headers) as websocket:
            self.ws = websocket
            await self.on_open()
            await self.handler()

    async def on_open(self):
        """Callback when WebSocket connection is opened."""
        print("WebSocket connection opened.")
        await self.subscribe_to_tickers()

    async def subscribe_to_tickers(self):
        """Subscribe to ticker updates for all markets."""
        subscription_message = {
            "id": self.message_id,
            "cmd": "subscribe",
            "params": {
                "channels": ["ticker"]
            }
        }
        await self.ws.send(json.dumps(subscription_message))
        self.message_id += 1

    async def handler(self):
        """Handle incoming messages."""
        try:
            async for message in self.ws:
                await self.on_message(message)
        except websockets.ConnectionClosed as e:
            await self.on_close(e.code, e.reason)
        except Exception as e:
            await self.on_error(e)

    async def on_message(self, message):
        """Callback for handling incoming messages."""
        print("Received message:", message)

    async def on_error(self, error):
        """Callback for handling errors."""
        print("WebSocket error:", error)

    async def on_close(self, close_status_code, close_msg):
        """Callback when WebSocket connection is closed."""
        print("WebSocket connection closed with code:", close_status_code, "and message:", close_msg)