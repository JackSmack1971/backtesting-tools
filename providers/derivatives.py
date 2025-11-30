import requests
from typing import Tuple, Optional

class DerivativesProvider:
    def __init__(self):
        self.binance_base = "https://fapi.binance.com"
        # Add other exchanges here if needed (e.g. Bybit, OKX public endpoints)

    def fetch_funding_and_oi(self, symbol: str = "BTCUSDT") -> Tuple[float, Optional[float], Optional[float]]:
        """
        Return (funding_rate, current_OI, OI_change_pct_approx).
        Returns (0.0, None, None) on failure.
        """
        funding_rate = 0.0
        current_oi = None
        oi_change_pct = None

        # 1. Funding Rate
        try:
            url = f"{self.binance_base}/fapi/v1/premiumIndex"
            resp = requests.get(url, params={"symbol": symbol}, timeout=5).json()
            funding_rate = float(resp["lastFundingRate"])
        except Exception:
            pass # Keep 0.0 or try fallback

        # 2. Open Interest
        try:
            url = f"{self.binance_base}/futures/data/openInterestHist"
            resp = requests.get(url, params={"symbol": symbol, "period": "1h", "limit": 24}, timeout=5).json()
            if resp:
                current_oi = float(resp[-1]["sumOpenInterest"])
                first_oi = float(resp[0]["sumOpenInterest"])
                oi_change_pct = (current_oi - first_oi) / first_oi * 100 if first_oi != 0 else 0.0
        except Exception:
            pass

        return funding_rate, current_oi, oi_change_pct
