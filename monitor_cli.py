import argparse
import pandas as pd
from data_loader import load_data, fetch_sample_data
from backtest_engine import compute_indicators
from thesis_config import ThesisLevels, Thresholds
from metrics_fetcher import fetch_funding_and_oi, fetch_btc_dominance_and_pairs, fetch_fear_greed
from scenario_engine import evaluate_scenarios

def main():
    parser = argparse.ArgumentParser(description="Microanalyst Live Thesis Monitor")
    parser.add_argument("--file", type=str, default="data/BTCUSDT_1h.csv",
                        help="Local CSV to update/read (will fetch if missing)")
    parser.add_argument("--symbol", type=str, default="BTCUSDT")
    parser.add_argument("--interval", type=str, default="1h")
    args = parser.parse_args()

    # 1) Load or fetch latest OHLCV (you could extend to append new candles)
    df = load_data(args.file, symbol=args.symbol, interval=args.interval)
    if df.empty:
        print("No data available, fetching sample...")
        df = fetch_sample_data(symbol=args.symbol, interval=args.interval, limit=1000, save_path=args.file)

    if df.empty:
        print("Still no data, exiting.")
        return

    # 2) Compute BB + ATR using your existing logic
    df = compute_indicators(df)

    # 3) Fetch external metrics
    print("Fetching live metrics...")
    funding_rate, oi, oi_change = fetch_funding_and_oi(symbol=args.symbol)
    btc_dom, eth_btc, sol_btc = fetch_btc_dominance_and_pairs()
    fear_value, fear_label = fetch_fear_greed()

    # 4) Evaluate scenarios
    levels = ThesisLevels()
    thresholds = Thresholds()
    eval_res = evaluate_scenarios(
        df,
        levels=levels,
        thresholds=thresholds,
        funding_rate=funding_rate,
        btc_dom=btc_dom,
        fear_value=fear_value,
    )

    if not eval_res:
        print("Error evaluating scenarios.")
        return

    # 5) Print dashboard
    last_idx = df.index[-1]
    print("=" * 80)
    print(f"Microanalyst Monitor @ {last_idx} (close)")
    print(f"Price: {eval_res['price']:.2f}")
    print(f"ATR%: {eval_res['atr_pct'] * 100 if eval_res['atr_pct'] else float('nan'):.3f}% "
          f"(compression={eval_res['compression']})")
    print(f"Position in BB (0=lower,1=upper): {eval_res['price_pos_in_bb']:.2f}")
    print()
    print(f"Funding (Binance): {funding_rate:.5f}  |  OI change (~24h proxy): {oi_change if oi_change is not None else 'N/A'}%")
    print(f"BTC dominance: {btc_dom:.2f}%  |  ETH/BTC: {eth_btc:.6f}  |  SOL/BTC: {sol_btc:.6f}")
    print(f"Fear & Greed: {fear_value} ({fear_label})  -> {eval_res['sentiment_tag']}")
    print()
    print("Scenario flags:", ", ".join(eval_res["scenario_flags"]))
    print("Rotation phase:", eval_res["rotation_phase"])
    print("=" * 80)

if __name__ == "__main__":
    main()
