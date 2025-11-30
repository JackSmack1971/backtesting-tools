import argparse
import pandas as pd
from providers.market_data import MarketDataProvider
from backtest_engine import compute_indicators
from thesis_config import ThesisLevels, Thresholds
from metrics_fetcher import fetch_funding_and_oi, fetch_btc_dominance_and_pairs, fetch_fear_greed
from scenario_engine import evaluate_scenarios
from alt_scanner import AltScanner
from risk_engine import RiskEngine
from logger import SignalLogger
from alert_system import AlertSystem

def main():
    parser = argparse.ArgumentParser(description="Microanalyst Live Thesis Monitor")
    parser.add_argument("--symbol", type=str, default="BTCUSDT")
    parser.add_argument("--interval", type=str, default="1h")
    parser.add_argument("--risk_stop", type=float, default=0.0, help="Stop loss for risk calc")
    parser.add_argument("--webhook", type=str, default=None, help="Webhook URL for alerts")
    args = parser.parse_args()

    # 1. Data
    provider = MarketDataProvider()
    df = provider.fetch_ohlcv(args.symbol, args.interval)
    
    if df.empty:
        print("No data available.")
        return

    # 2. Indicators
    df = compute_indicators(df)

    # 3. Metrics
    print("Fetching live metrics...")
    funding_rate, oi, oi_change = fetch_funding_and_oi(args.symbol)
    btc_dom, eth_btc, sol_btc = fetch_btc_dominance_and_pairs()
    fear_value, fear_label = fetch_fear_greed()

    # 4. Scenarios
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

    # 5. Alt Scan (Optional, maybe flag to enable?)
    print("Scanning alts...")
    scanner = AltScanner()
    # We pass a small slice of BTC df to scanner for comparison
    alt_df = scanner.scan_rotation(df.tail(48))

    # 6. Risk Calc
    risk_res = {}
    if args.risk_stop > 0:
        risk_engine = RiskEngine()
        risk_res = risk_engine.calculate_position(eval_res['price'], args.risk_stop)

    # 7. Logging & Alerting
    logger = SignalLogger()
    logger_data = eval_res.copy()
    logger_data['funding'] = funding_rate
    logger_data['btc_dom'] = btc_dom
    logger.log_run(logger_data)
    
    alerter = AlertSystem(webhook_url=args.webhook)
    alerter.check_and_alert(eval_res)

    # 8. Dashboard Output
    last_idx = df.index[-1]
    print("=" * 80)
    print(f"Microanalyst Monitor @ {last_idx} (close)")
    print(f"Price: {eval_res['price']:.2f}")
    print(f"ATR%: {eval_res['atr_pct'] * 100 if eval_res['atr_pct'] else float('nan'):.3f}% "
          f"(compression={eval_res['compression']})")
    print(f"Liq Pulse: {eval_res.get('liquidation_pulse', 'N/A')}")
    print()
    print(f"Funding: {funding_rate:.5f}  |  OI Change: {oi_change if oi_change is not None else 'N/A'}%")
    print(f"Dominance: BTC {btc_dom:.1f}% | ETH/BTC {eth_btc:.5f} | SOL/BTC {sol_btc:.5f}")
    print(f"Sentiment: {fear_value} ({fear_label})")
    print()
    print("Flags:", ", ".join(eval_res["scenario_flags"]))
    print("Rotation:", eval_res["rotation_phase"])
    
    if not alt_df.empty:
        print("\n--- Alt Rotation (Top 3 vs BTC) ---")
        print(alt_df.head(3)[['symbol', 'pct_change_24h', 'rel_strength_btc']].to_string(index=False))

    if risk_res:
        print("\n--- Risk Calculator ---")
        if "error" in risk_res:
            print(f"Error: {risk_res['error']}")
        else:
            print(f"Stop: {risk_res['stop']} ({risk_res['stop_distance_pct']:.2f}%)")
            print(f"Size: {risk_res['quantity']:.4f} BTC (${risk_res['position_notional']:.0f})")
            print(f"Lev: {risk_res['leverage']:.2f}x")

    print("=" * 80)
