from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from app.services.metatrader_service import mt5_gateway
from app.services.risk_engine import risk_engine

router = APIRouter(prefix="/api/v1/execution", tags=["Trade Execution"])

class ExecuteOrderRequest(BaseModel):
    account_id: str = Field(default="account1")
    symbol: str = Field(..., example="EURUSD")
    action: str = Field(..., example="BUY")  # BUY or SELL
    account_balance: float = Field(..., gt=0)
    quantum_confidence: float = Field(..., ge=0, le=100)
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    comment: Optional[str] = "KD Quantum Auto Trade"

@router.post("/execute")
async def execute_trade(payload: ExecuteOrderRequest):
    # 1. Calculate dynamic Quantum Kelly lot size
    risk_data = risk_engine.calculate_kelly_position_size(
        account_balance=payload.account_balance,
        win_rate=0.55,
        risk_reward_ratio=1.5,
        quantum_confidence=payload.quantum_confidence
    )
    
    calculated_lots = risk_data.get("recommended_lots", 0.01)

    # 2. Dispatch order to MT5 Gateway
    trade_result = mt5_gateway.send_order(
        account_id=payload.account_id,
        symbol=payload.symbol.upper(),
        action=payload.action.upper(),
        volume=calculated_lots,
        stop_loss=payload.stop_loss,
        take_profit=payload.take_profit,
        comment=payload.comment
    )

    if trade_result.get("status") != "EXECUTED":
        raise HTTPException(status_code=500, detail=trade_result.get("message", "Execution failed"))

    return {
        "status": "SUCCESS",
        "execution_details": trade_result,
        "risk_metrics": risk_data
    }

@router.get("/positions/{account_id}")
async def get_open_positions(account_id: str):
    positions = mt5_gateway.get_open_positions(account_id)
    return {"status": "SUCCESS", "account_id": account_id, "positions": positions}

@router.post("/close/{trade_id}")
async def close_position(trade_id: str, account_id: str = "account1"):
    result = mt5_gateway.close_position(account_id=account_id, trade_id=trade_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    return {"status": "SUCCESS", "result": result}
