import pandas as pd
import argparse
from data_loader import load_data
from backtest_engine import compute_indicators, identify_squeeze_periods, run_breakout_tests, summarize_results

def main():
    parser = argparse.ArgumentParser(description="Bollinger Band Squeeze Backtester")
    parser.add_argument("--file", type=str, default="data/BTCUSDT_1h.csv", help="Path to CSV data file")
    parser.add_argument("--symbol", type=str, default="BTCUSDT", help="Symbol to fetch if file missing")
    parser.add_argument("--interval", type=str, default="1h", help="Timeframe interval")
    parser.add_argument("--bb_window", type=int, default=20, help="Bollinger Band window")
    parser.add_argument("--bb_std", type=float, default=2.0, help="Bollinger Band std dev multiplier")
    parser.add_argument("--atr_window", type=int, default=14, help="ATR window")
    parser.add_argument("--bw_quantile", type=float, default=0.10, help="Bandwidth quantile threshold")
    parser.add_argument("--atr_quantile", type=float, default=0.10, help="ATR quantile threshold")
    
    args = parser.parse_args()
    
    print(f"--- Starting Backtest for {args.symbol} {args.interval} ---")
    
    # 1. Load Data
    df = load_data(args.file, symbol=args.symbol, interval=args.interval)
    if df.empty:
        print("No data loaded. Exiting.")
        return

    print(f"Loaded {len(df)} bars from {df.index[0]} to {df.index[-1]}")

    # 2. Compute Indicators
    df = compute_indicators(df, bb_window=args.bb_window, bb_std_multiplier=args.bb_std, atr_window=args.atr_window)
    
    # 3. Identify Squeezes
    df = identify_squeeze_periods(df, bandwidth_threshold_quantile=args.bw_quantile, atr_threshold_quantile=args.atr_quantile)
    
    squeeze_count = df['squeeze'].sum()
    squeeze_events = df['squeeze_end'].sum()
    print(f"Identified {squeeze_count} squeeze bars and {squeeze_events} squeeze breakout events.")
    
    if squeeze_events == 0:
        print("No squeezes found. Try adjusting thresholds.")
        return

    # 4. Run Breakout Tests
    # Hold periods: 1h, 4h, 12h, 24h, 7d (168h)
    hold_periods = [1, 4, 12, 24, 168]
    results_df = run_breakout_tests(df, hold_periods=hold_periods)
    
    if results_df.empty:
        print("No valid breakout tests completed (possibly not enough data after squeezes).")
        return

    # 5. Summarize Results
    summary = summarize_results(results_df)
    
    print("\n--- Backtest Results Summary ---")
    # Set pandas display options to show all columns
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print(summary)
    
    # Optional: Save results
    results_df.to_csv("backtest_results.csv", index=False)
    print("\nDetailed results saved to backtest_results.csv")

if __name__ == "__main__":
    main()
