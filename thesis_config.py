from dataclasses import dataclass

@dataclass
class ThesisLevels:
    mini_support_low: float = 90500
    mini_support_high: float = 90750
    primary_support_low: float = 87600
    primary_support_high: float = 88300
    flush_low: float = 85800
    flush_high: float = 86200
    invalidation_level: float = 82000

@dataclass
class Thresholds:
    funding_strong_negative: float = -0.0005   # -0.05%/8h
    funding_strong_positive: float = 0.0005
    atr_low_percent: float = 0.004             # ATR < 0.4% of price = compression
    btc_dom_phase2: float = 58.0
    btc_dom_phase1: float = 60.0
    fear_extreme: int = 25
