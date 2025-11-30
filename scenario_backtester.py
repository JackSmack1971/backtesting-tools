import pandas as pd
import argparse
from providers.market_data import MarketDataProvider
from backtest_engine import compute_indicators
from scenario_engine import evaluate_scenarios
from thesis_config import ThesisLevels, Thresholds

def run_scenario_backtest(symbol="BTCUSDT", interval="1h", limit=1000):
    provider = MarketDataProvider()
    df = provider.fetch_ohlcv(symbol, interval, limit)
    
    if df.empty:
        print("No data.")
        return

    df = compute_indicators(df)
    
    levels = ThesisLevels()
    thresholds = Thresholds()
    
    results = []
    
    # Iterate through history
    # Note: This is slow for large datasets but fine for "microanalyst" checks
    for i in range(50, len(df)):
        slice_df = df.iloc[:i+1]
        
        # We don't have historical funding/sentiment in this simple backtester
        # So we mock them or assume neutral to test purely the PRICE/VOL logic
        res = evaluate_scenarios(
            slice_df, 
            levels, 
            thresholds, 
            funding_rate=0.0, 
            btc_dom=55.0, 
            fear_value=50
        )
        
        results.append({
            "timestamp": slice_df.index[-1],
            "price": res["price"],
            "flags": ";".join(res["scenario_flags"]),
            "liq_pulse": res.get("liquidation_pulse", "NORMAL")
        })
        
    results_df = pd.DataFrame(results).set_index("timestamp")
    
    # Count occurrences
    print("--- Scenario Flags Frequency ---")
    all_flags = []
    for flags in results_df["flags"]:
        all_flags.extend(flags.split(";"))
    print(pd.Series(all_flags).value_counts())
    
    print("\n--- Liquidation Pulse Frequency ---")
    print(results_df["liq_pulse"].value_counts())
    
    return results_df

if __name__ == "__main__":
    run_scenario_backtest()
