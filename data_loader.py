import pandas as pd
import requests
import os
from datetime import datetime

def fetch_sample_data(symbol="BTCUSDT", interval="1h", limit=1000, save_path=None):
    """
    Fetch sample OHLC data from Binance public API.
    NOTE: This is for demonstration purposes. For a full backtest, use a complete historical dataset.
    """
    base_url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    
    print(f"Fetching {limit} candles for {symbol} {interval} from Binance...")
    
    urls = [
        "https://api.binance.com/api/v3/klines",
        "https://api.binance.us/api/v3/klines"
    ]
    
    for base_url in urls:
        try:
            print(f"Trying {base_url}...")
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            break # Success
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 451:
                print(f"Region restricted (451) for {base_url}. Trying next...")
                continue
            else:
                print(f"HTTP Error {e} for {base_url}")
                continue
        except Exception as e:
            print(f"Error {e} for {base_url}")
            continue
    else:
        print("Failed to fetch data from all sources.")
        return pd.DataFrame()
        
    # Binance response format: 
    # [
    #   [
    #     1499040000000,      // Open time
    #     "0.01634790",       // Open
    #     "0.80000000",       // High
    #     "0.01575800",       // Low
    #     "0.01577100",       // Close
    #     "148976.11427815",  // Volume
    #     ...
    #   ]
    # ]
    
    try:
        df = pd.DataFrame(data, columns=[
            "open_time", "open", "high", "low", "close", "volume", 
            "close_time", "quote_asset_volume", "number_of_trades", 
            "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
        ])
        
        df["timestamp"] = pd.to_datetime(df["open_time"], unit="ms")
        df = df[["timestamp", "open", "high", "low", "close", "volume"]]
        
        # Convert to numeric
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            
        df = df.set_index("timestamp").sort_index()
        
        if save_path:
            # Ensure directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            df.to_csv(save_path)
            print(f"Saved sample data to {save_path}")
            
        return df
        
    except Exception as e:
        print(f"Error processing data: {e}")
        return pd.DataFrame()

def load_data(filepath, symbol="BTCUSDT", interval="1h"):
    """
    Load historical OHLC data from CSV. 
    If file doesn't exist, try to fetch sample data.
    """
    if not os.path.exists(filepath):
        print(f"File {filepath} not found. Attempting to fetch sample data...")
        return fetch_sample_data(symbol, interval, limit=1000, save_path=filepath)
    
    try:
        df = pd.read_csv(filepath)
        # Check if 'timestamp' or 'Date' exists
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
        elif 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.set_index('Date')
        
        # Ensure columns are lower case for consistency
        df.columns = [c.lower() for c in df.columns]
        
        # Ensure required columns exist
        required = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required):
            raise ValueError(f"Dataframe missing required columns: {required}")
            
        df = df.sort_index()
        return df
    except Exception as e:
        print(f"Error loading data from {filepath}: {e}")
        return pd.DataFrame()
