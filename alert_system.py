import requests
import json

class AlertSystem:
    def __init__(self, webhook_url=None):
        self.webhook_url = webhook_url

    def check_and_alert(self, scenario_result: dict):
        """
        Check flags and send alert if critical.
        """
        flags = scenario_result.get("scenario_flags", [])
        liq_pulse = scenario_result.get("liquidation_pulse", "NORMAL")
        
        critical_flags = [
            "SCENARIO_2_FLUSH_FAVORED", 
            "SCENARIO_3_BREAKDOWN_RISK",
            "SCENARIO_4_BREAKOUT_POTENTIAL",
            "LIQUIDATION_PULSE_DETECTED"
        ]
        
        triggered = [f for f in flags if f in critical_flags]
        if liq_pulse != "NORMAL":
            triggered.append(f"LIQ_PULSE_{liq_pulse}")
            
        if triggered:
            msg = f"🚨 ALERT: {', '.join(triggered)} @ {scenario_result.get('price')}"
            self._send(msg)
            return True
        return False

    def _send(self, message):
        print(f"\n[ALERT SYSTEM] {message}\n")
        if self.webhook_url:
            try:
                requests.post(self.webhook_url, json={"content": message})
            except Exception as e:
                print(f"Failed to send webhook: {e}")
