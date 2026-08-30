import math
from typing import Dict, Any

class QuantumRiskEngine:
    def __init__(self, max_account_risk_pct: float = 0.02, max_drawdown_limit: float = 0.15):
        self.max_account_risk_pct = max_account_risk_pct  # Max 2% risk per trade
        self.max_drawdown_limit = max_drawdown_limit      # 15% system stop-out

    def calculate_kelly_position_size(
        self,
        account_balance: float,
        win_rate: float,
        risk_reward_ratio: float,
        quantum_confidence: float
    ) -> Dict[str, Any]:
        """
        Calculates optimal position size using the Fractional Quantum Kelly Criterion.
        Scales risk down dynamically if quantum signal confidence drops.
        """
        if risk_reward_ratio <= 0 or win_rate <= 0:
            return {"recommended_lots": 0.01, "risk_amount": 0.0, "kelly_fraction": 0.0}

        # Standard Kelly Criterion formula: f* = (p * b - q) / b
        p = win_rate
        q = 1.0 - p
        b = risk_reward_ratio
        kelly_fraction = (p * b - q) / b

        if kelly_fraction <= 0:
            return {
                "recommended_lots": 0.01,
                "risk_amount": 0.0,
                "kelly_fraction": 0.0,
                "status": "NO_TRADE_RECOMMENDED"
            }

        # Apply Quantum Fractional Scaling (Half-Kelly weighted by QPU Confidence)
        confidence_factor = min(max(quantum_confidence / 100.0, 0.5), 1.0)
        scaled_kelly = (kelly_fraction * 0.5) * confidence_factor

        # Hard cap at max account risk setting
        effective_risk_pct = min(scaled_kelly, self.max_account_risk_pct)
        risk_amount = round(account_balance * effective_risk_pct, 2)

        # Standard lot calculation (assuming standard 100k unit contract & 1% = 100 pips approx)
        estimated_lots = round(risk_amount / 1000.0, 2)
        recommended_lots = max(0.01, min(estimated_lots, 10.0))  # Clamp between 0.01 and 10.0 lots

        return {
            "recommended_lots": recommended_lots,
            "risk_amount": risk_amount,
            "risk_percentage": round(effective_risk_pct * 100, 2),
            "raw_kelly": round(kelly_fraction, 4),
            "quantum_scaling_factor": round(confidence_factor, 2),
            "status": "CALCULATED"
        }

risk_engine = QuantumRiskEngine()
