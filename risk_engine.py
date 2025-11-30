from dataclasses import dataclass

@dataclass
class RiskConfig:
    account_size: float = 10000.0
    risk_per_trade_pct: float = 1.0  # 1% risk
    max_leverage: float = 5.0

class RiskEngine:
    def __init__(self, config: RiskConfig = RiskConfig()):
        self.config = config

    def calculate_position(self, entry_price: float, stop_loss: float) -> dict:
        """
        Calculate position size based on risk % and stop distance.
        """
        if entry_price <= 0 or stop_loss <= 0:
            return {"error": "Invalid price/stop"}
            
        risk_amount = self.config.account_size * (self.config.risk_per_trade_pct / 100.0)
        stop_distance_pct = abs(entry_price - stop_loss) / entry_price
        
        if stop_distance_pct == 0:
            return {"error": "Stop loss equals entry price"}
            
        position_notional = risk_amount / stop_distance_pct
        leverage = position_notional / self.config.account_size
        
        # Cap leverage
        if leverage > self.config.max_leverage:
            position_notional = self.config.account_size * self.config.max_leverage
            leverage = self.config.max_leverage
            # Recalculate risk amount (it will be less than target)
            risk_amount = position_notional * stop_distance_pct

        quantity = position_notional / entry_price
        
        return {
            "entry": entry_price,
            "stop": stop_loss,
            "risk_amount": risk_amount,
            "position_notional": position_notional,
            "quantity": quantity,
            "leverage": leverage,
            "stop_distance_pct": stop_distance_pct * 100
        }
