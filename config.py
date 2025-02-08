import os
from cryptography.hazmat.primitives import serialization
import asyncio
from clients import KalshiHttpClient, KalshiWebSocketClient, Environment

env = Environment.PROD # toggle environment here
KEYID = 'df198041-cea6-49ef-8e8b-639c9412258e'
KEYFILE = os.path.expanduser("~/EkklesKalshi.pem")


list_markets = [
    {'ticker' : 'KXGREENLAND'}
    ]
market_id = 'KXGREENLAND'