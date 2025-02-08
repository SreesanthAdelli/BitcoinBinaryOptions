# BitcoinBinaryOptions
This project focuses on an automated Bitcoin binary options trading system that uses real-time market data and algorithmic strategies to predict price movements. It incorporates risk management tools to optimize short-term trades in the volatile Bitcoin market. Sadly slightly more advanced models are being used, so it is not profitable.

This project implements an automated trading system for **Bitcoin binary options** on **Kalshi**. The system uses real-time market data, the **Black-Scholes equation** to price options optimally, and executes trades at the optimal prices. It also incorporates **implied volatility** derived from existing Bitcoin options.

Several utility functions have been written to simplify API integration with Kalshi, along with example code for basic trading strategies.

## Features
- **Real-Time Market Data**: Fetches live Bitcoin prices from exchanges for accurate pricing.
- **Black-Scholes Pricing**: Utilizes the Black-Scholes equation to calculate optimal option prices.
- **Implied Volatility**: Uses implied volatility from existing Bitcoin options to inform price calculations and predictions.
- **Kalshi Trading**: Executes binary options trades on Kalshi based on optimal pricing.
- **API Integration**: Includes functions to simplify integration with the Kalshi API.
- **Example Strategies**: Provides sample code for basic trading strategies.

## Getting Started
1. Clone the repository:  
   `git clone https://github.com/SreesanthAdelli/BitcoinBinaryOptions.git`
2. Install dependencies:  
   `pip install -r requirements.txt`
3. Set up your Kalshi API keys for trading, and the path to the PEM file
5. Run the trading system:  
   `python main.py`

## Configuration
- Modify `config.py` to add your Kalshi API keys and any other necessary settings.


## Contributing
Feel free to fork this repository, submit issues, and create pull requests to improve the project.

