import requests
import pandas as pd
import os
from typing import Optional

class MarketDataProvider:
    def __init__(self):
        self.sources = [
            "https://api.binance.com/api/v3/klines",
            "https://api.binance.us/api/v3/klines"
        ]

    def fetch_ohlcv(self, symbol: str = "BTCUSDT", interval: str = "1h", limit: int = 1000) -> pd.DataFrame:
        """
        Fetch OHLCV data from available sources.
        Returns empty DataFrame on failure.
        """
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        
        for base_url in self.sources:
            try:
                response = requests.get(base_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                return self._parse_binance_response(data)
            except Exception as e:
                # print(f"Provider error ({base_url}): {e}")
                continue
                
        return pd.DataFrame()

    def _parse_binance_response(self, data: list) -> pd.DataFrame:
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data, columns=[
            "open_time", "open", "high", "low", "close", "volume", 
            "close_time", "quote_asset_volume", "number_of_trades", 
            "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
        ])
        
        df["timestamp"] = pd.to_datetime(df["open_time"], unit="ms")
        df = df[["timestamp", "open", "high", "low", "close", "volume"]]
        
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            
        return df.set_index("timestamp").sort_index()

    def load_or_fetch(self, filepath: str, symbol: str = "BTCUSDT", interval: str = "1h") -> pd.DataFrame:
        """
        Load from CSV if exists, else fetch and save.
        """
        if os.path.exists(filepath):
            try:
                df = pd.read_csv(filepath)
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df = df.set_index('timestamp')
                elif 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'])
                    df = df.set_index('Date')
                df.columns = [c.lower() for c in df.columns]
                return df.sort_index()
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
        
        print(f"Fetching {symbol} data...")
        df = self.fetch_ohlcv(symbol, interval)
        if not df.empty and filepath:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            df.to_csv(filepath)
            print(f"Saved to {filepath}")
            
        return df
