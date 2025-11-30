import requests
from typing import Tuple, Optional

BINANCE_FUTURES_BASE = "https://fapi.binance.com"
COINGECKO_BASE = "https://api.coingecko.com/api/v3"
FNG_URL = "https://api.alternative.me/fng/?limit=1"

def fetch_funding_and_oi(symbol: str = "BTCUSDT") -> Tuple[float, Optional[float], Optional[float]]:
    """Return (funding_rate, current_OI, OI_change_pct_approx)."""
    funding_url = f"{BINANCE_FUTURES_BASE}/fapi/v1/premiumIndex"
    oi_url = f"{BINANCE_FUTURES_BASE}/futures/data/openInterestHist"

    try:
        funding_resp = requests.get(funding_url, params={"symbol": symbol}, timeout=10).json()
        funding_rate = float(funding_resp["lastFundingRate"])
    except Exception as e:
        print(f"Error fetching funding: {e}")
        funding_rate = 0.0

    try:
        oi_resp = requests.get(oi_url, params={"symbol": symbol, "period": "1h", "limit": 24}, timeout=10).json()
        if not oi_resp:
            return funding_rate, None, None

        current_oi = float(oi_resp[-1]["sumOpenInterest"])
        first_oi = float(oi_resp[0]["sumOpenInterest"])
        oi_change_pct = (current_oi - first_oi) / first_oi * 100 if first_oi != 0 else None
    except Exception as e:
        print(f"Error fetching OI: {e}")
        current_oi, oi_change_pct = None, None

    return funding_rate, current_oi, oi_change_pct

def fetch_btc_dominance_and_pairs() -> Tuple[float, float, float]:
    """Return (BTC_dominance_pct, ETH/BTC, SOL/BTC) from CoinGecko."""
    try:
        global_resp = requests.get(f"{COINGECKO_BASE}/global", timeout=10).json()
        btc_dom = float(global_resp["data"]["market_cap_percentage"]["btc"])

        prices = requests.get(
            f"{COINGECKO_BASE}/simple/price",
            params={"ids": "bitcoin,ethereum,solana", "vs_currencies": "btc"},
            timeout=10
        ).json()

        eth_btc = float(prices["ethereum"]["btc"])
        sol_btc = float(prices["solana"]["btc"])
    except Exception as e:
        print(f"Error fetching CoinGecko data: {e}")
        return 0.0, 0.0, 0.0
        
    return btc_dom, eth_btc, sol_btc

def fetch_fear_greed() -> Tuple[int, str]:
    """Fear & Greed index (0–100) and label."""
    try:
        data = requests.get(FNG_URL, timeout=10).json()
        value = int(data["data"][0]["value"])
        label = data["data"][0]["value_classification"]
    except Exception as e:
        print(f"Error fetching Fear & Greed: {e}")
        return 50, "Unknown"
        
    return value, label
