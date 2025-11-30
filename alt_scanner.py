import pandas as pd
from providers.market_data import MarketDataProvider

class AltScanner:
    def __init__(self):
        self.provider = MarketDataProvider()
        self.watchlist = ["ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT"]

    def scan_rotation(self, btc_df: pd.DataFrame) -> pd.DataFrame:
        """
        Compare alts to BTC performance over last 24h.
        Returns DataFrame with columns: [symbol, pct_change_24h, rel_strength_btc]
        """
        if btc_df.empty:
            return pd.DataFrame()
            
        btc_close = btc_df.iloc[-1]['close']
        btc_open_24h = btc_df.iloc[-24]['close'] if len(btc_df) >= 24 else btc_df.iloc[0]['close']
        btc_perf = (btc_close - btc_open_24h) / btc_open_24h * 100
        
        results = []
        
        for symbol in self.watchlist:
            # We need to fetch data for each alt. 
            # In a real app, we'd cache this or fetch in parallel.
            # For this CLI tool, sequential fetch is acceptable but slow.
            # We'll fetch just enough data (e.g. 48h) to be fast.
            df = self.provider.fetch_ohlcv(symbol, interval="1h", limit=48)
            if df.empty:
                continue
                
            last_close = df.iloc[-1]['close']
            open_24h = df.iloc[-24]['close'] if len(df) >= 24 else df.iloc[0]['close']
            perf = (last_close - open_24h) / open_24h * 100
            
            rel_strength = perf - btc_perf
            
            results.append({
                "symbol": symbol,
                "price": last_close,
                "pct_change_24h": perf,
                "rel_strength_btc": rel_strength
            })
            
        return pd.DataFrame(results).sort_values("rel_strength_btc", ascending=False)
