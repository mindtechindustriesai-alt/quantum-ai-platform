from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.services.risk_engine import risk_engine

router = APIRouter(prefix="/api/v1/risk", tags=["Risk Management"])

class RiskCalculationRequest(BaseModel):
    account_balance: float = Field(..., gt=0, description="Current account equity")
    win_rate: float = Field(default=0.55, ge=0.0, le=1.0, description="Historical strategy win rate (0.0 to 1.0)")
    risk_reward_ratio: float = Field(default=1.5, gt=0, description="Take Profit / Stop Loss ratio")
    quantum_confidence: float = Field(..., ge=0.0, le=100.0, description="Confidence score from Quantum Signal")

@router.post("/calculate-size")
def calculate_trade_risk(payload: RiskCalculationRequest):
    try:
        result = risk_engine.calculate_kelly_position_size(
            account_balance=payload.account_balance,
            win_rate=payload.win_rate,
            risk_reward_ratio=payload.risk_reward_ratio,
            quantum_confidence=payload.quantum_confidence
        )
        return {"status": "SUCCESS", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
