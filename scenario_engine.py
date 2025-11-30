from typing import Dict, List
import math
import pandas as pd
from thesis_config import ThesisLevels, Thresholds

def evaluate_scenarios(
    df: pd.DataFrame,
    levels: ThesisLevels,
    thresholds: Thresholds,
    funding_rate: float,
    btc_dom: float,
    fear_value: int,
) -> Dict[str, object]:
    """
    Use the latest bar + side metrics to classify:
    - scenario hints (S1/S2/S3/S4)
    - rotation phase (Phase 1/2/off)
    """
    if df.empty:
        return {}
        
    last = df.iloc[-1]
    price = float(last["close"])
    atr = float(last.get("atr", float("nan")))
    bb_upper = float(last.get("bb_upper", float("nan")))
    bb_lower = float(last.get("bb_lower", float("nan")))

    bb_width = bb_upper - bb_lower if not math.isnan(bb_upper) and not math.isnan(bb_lower) else float("nan")
    price_pos = (price - bb_lower) / bb_width if bb_width and not math.isnan(bb_width) else 0.5
    atr_pct = atr / price if price and not math.isnan(atr) else float("nan")

    compression = not math.isnan(atr_pct) and atr_pct < thresholds.atr_low_percent
    in_mini_support = levels.mini_support_low <= price <= levels.mini_support_high
    above_primary = price >= levels.primary_support_low
    in_flush = levels.flush_low <= price <= levels.flush_high

    scenario_flags: List[str] = []

    if price < levels.invalidation_level:
        scenario_flags.append("SCENARIO_3_BREAKDOWN_RISK")
    elif in_flush:
        if funding_rate < thresholds.funding_strong_negative:
            scenario_flags.append("SCENARIO_2_FLUSH_FAVORED")
        else:
            scenario_flags.append("SCENARIO_2_OR_NOISE")
    elif above_primary and compression:
        scenario_flags.append("SCENARIO_1_BASE_BUILDING")
        if price_pos > 0.5:
            scenario_flags.append("SCENARIO_4_BREAKOUT_POTENTIAL")
    else:
        scenario_flags.append("MID_RANGE_UNCLEAR")

    # Rotation
    if btc_dom < thresholds.btc_dom_phase2:
        rotation_phase = "PHASE_2 (broad rotation likely)"
    elif btc_dom < thresholds.btc_dom_phase1:
        rotation_phase = "PHASE_1 (majors rotation ON)"
    else:
        rotation_phase = "NO_ROTATION (BTC dominance high)"

    if fear_value <= thresholds.fear_extreme:
        sentiment_tag = "EXTREME_FEAR"
    else:
        sentiment_tag = "NORMAL_SENTIMENT"

    return {
        "price": price,
        "atr_pct": atr_pct,
        "price_pos_in_bb": price_pos,
        "compression": compression,
        "scenario_flags": scenario_flags,
        "rotation_phase": rotation_phase,
        "sentiment_tag": sentiment_tag,
    }
