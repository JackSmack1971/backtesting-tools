from providers.derivatives import DerivativesProvider
from providers.sentiment import SentimentProvider
import requests

# Backward compatibility wrapper
def fetch_funding_and_oi(symbol: str = "BTCUSDT"):
    return DerivativesProvider().fetch_funding_and_oi(symbol)

def fetch_fear_greed():
    return SentimentProvider().fetch_fear_greed()

def fetch_btc_dominance_and_pairs():
    # Keep CoinGecko logic here or move to a new provider if needed.
    # For now, let's leave it as is but wrap it cleanly.
    try:
        COINGECKO_BASE = "https://api.coingecko.com/api/v3"
        global_resp = requests.get(f"{COINGECKO_BASE}/global", timeout=10).json()
        btc_dom = float(global_resp["data"]["market_cap_percentage"]["btc"])

        prices = requests.get(
            f"{COINGECKO_BASE}/simple/price",
            params={"ids": "bitcoin,ethereum,solana", "vs_currencies": "btc"},
            timeout=10
        ).json()

        eth_btc = float(prices["ethereum"]["btc"])
        sol_btc = float(prices["solana"]["btc"])
        return btc_dom, eth_btc, sol_btc
    except Exception as e:
        print(f"Error fetching CoinGecko data: {e}")
        return 0.0, 0.0, 0.0
