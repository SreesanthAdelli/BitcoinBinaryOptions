from clients import KalshiBaseClient, KalshiHttpClient
from config import KEYID, KEYFILE, env
import time
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization
from demo_strategy import trade_strategy
from ninetypercent import trade_ninetypercent
from dynamic_liquidity import dynamic_liquidity_provision
from bitcoinstrat import bitcoinstrat

try:
    with open(KEYFILE, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None  # Provide the password if your key is encrypted
        )
except FileNotFoundError:
    raise FileNotFoundError(f"Private key file not found at {KEYFILE}")
except Exception as e:
    raise Exception(f"Error loading private key: {str(e)}")



def run_trading_bot():
    # Establish connection to Kalshi by creating a KalshiClient instance
    client = KalshiHttpClient(
        key_id=KEYID,
        private_key=private_key,
        environment=env
    )
    


    bitcoinstrat(client=client, IV_percent=52, spread=0.03, refresh_rate=10)
    


if __name__ == '__main__':
    # Get current time and 24 hours from now in milliseconds
    run_trading_bot()

