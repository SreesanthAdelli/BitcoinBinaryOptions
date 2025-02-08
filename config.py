import os
from cryptography.hazmat.primitives import serialization
import asyncio
from clients import KalshiHttpClient, KalshiWebSocketClient, Environment

env = Environment.PROD # toggle environment here
KEYID = 'USE YOUR KEY ID' # Replace
KEYFILE = os.path.expanduser("~/EkklesKalshi.pem")


list_markets = [
    {'ticker' : 'KXGREENLAND'}
    ]
market_id = 'KXGREENLAND'
