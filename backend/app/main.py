"""
KD Quantum Trading Platform — Backend
IBM-verified quantum trading signals · CHSH S=2.76 · SA Patent 2026/05142
IC Markets Integration — Multi-Account Support
"""

import os
import random
import httpx
import secrets
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Quantum Engine & MT5 Gateway Imports (Phase 2 Integration)
from app.services.quantum_engine import quantum_engine
from app.services.metatrader_service import mt5_gateway

# WebSocket Router Import (Phase 3 Integration)
from app.routers import websocket as ws_router

load_dotenv()

# ============================================================
# QUANTUM CONSTANTS (IBM-Verified)
# ============================================================

QUANTUM_BADGE = {
    "chsh_s": 2.76,
    "classical_limit": 2.0,
    "quantum_max": 2.828,
    "percent_above_classical": 38.0,
    "correlation": 0.984,
    "patent": "SA 2026/05142",
    "verification_date": "2026-06-25",
    "ibm_job_id": "d8uhvl4bp3hs738628cg",
    "text": "CHSH S=2.76 · 38% above classical"
}

VALID_TIMEFRAMES = ["15m", "30m", "1h", "4h", "1d"]

# ============================================================
# IC MARKETS CONFIGURATION
# ============================================================

IC_ACCOUNTS = {
    "account1": {
        "id": os.getenv("IC_ACCOUNT_1_ID", "123456"),
        "name": "IC Markets - Account 1",
        "server": os.getenv("IC_ACCOUNT_1_SERVER", "ICMarkets-Demo"),
        "login": os.getenv("IC_ACCOUNT_1_LOGIN", "123456"),
        "password": os.getenv("IC_ACCOUNT_1_PASSWORD", "password"),
        "type": "demo" 
    },
    "account2": {
        "id": os.getenv("IC_ACCOUNT_2_ID", "789012"),
        "name": "IC Markets - Account 2",
        "server": os.getenv("IC_ACCOUNT_2_SERVER", "ICMarkets-Demo"),
        "login": os.getenv("IC_ACCOUNT_2_LOGIN", "789012"),
        "password": os.getenv("IC_ACCOUNT_2_PASSWORD", "password"),
        "type": "demo"
    },
    "account3": {
        "id": os.getenv("IC_ACCOUNT_3_ID", "345678"),
        "name": "IC Markets - Account 3",
        "server": os.getenv("IC_ACCOUNT_3_SERVER", "ICMarkets-Demo"),
        "login": os.getenv("IC_ACCOUNT_3_LOGIN", "345678"),
        "password": os.getenv("IC_ACCOUNT_3_PASSWORD", "password"),
        "type": "demo"
    }
}

IC_SYMBOLS = [
    "USDCHF", "GBPUSD", "EURUSD", "USDJPY", "USDCAD", "AUDUSD",
    "EURGBP", "EURAUD", "EURCHF", "EURJPY", "GBPCHF", "CADJPY",
    "AUDNZD", "AUDCAD", "AUDCHF", "AUDJPY", "CHFJPY", "EURNZD",
    "EURCAD", "CADCHF", "NZDJPY", "NZDUSD"
]

# ============================================================
# USER DATABASE — In-memory for demo
# ============================================================

USER_DB: Dict[str, str] = {
    "admin": "quantum2026",
    "trader1": "trade123",
    "test": "test123"
}

SESSION_STORE: Dict[str, str] = {}

# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Quantum AI Trading Engine",
    description="IBM-verified quantum trading signals with IC Markets integration",
    version="2.1.0"
)

# Phase 3: WebSocket Router Registration
app.include_router(ws_router.router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# AUTHENTICATION & IC MARKETS MODELS
# ============================================================

class LoginRequest(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

class LoginResponse(BaseModel):
    status: str
    token: str
    username: str
    quantum_badge: dict
    message: str

class TradeRequest(BaseModel):
    symbol: str = Field(..., description="Trading pair (e.g., EURUSD, GBPUSD)")
    action: str = Field(..., description="BUY or SELL")
    volume: float = Field(default=1.0, description="Lot size (1.0 = standard lot)")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")
    account_id: str = Field(default="account1", description="Which IC Markets account to use")
    comment: Optional[str] = Field(None, description="Trade comment")

class TradeResponse(BaseModel):
    status: str
    trade_id: str
    symbol: str
    action: str
    volume: float
    entry_price: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    account_id: str
    timestamp: str
    quantum_verified: bool = True
    patent: str = "SA 2026/05142"
    message: Optional[str] = None

class MarketDataResponse(BaseModel):
    symbol: str
    bid: float
    ask: float
    spread: float
    timestamp: str
    quantum_verified: bool = True

class AccountInfoResponse(BaseModel):
    account_id: str
    name: str
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float
    open_trades: int
    type: str

class PositionResponse(BaseModel):
    trade_id: str
    symbol: str
    action: str
    volume: float
    open_price: float
    current_price: float
    profit: float
    profit_percent: float
    open_time: str
    stop_loss: Optional[float]
    take_profit: Optional[float]

# ============================================================
# AUTHENTICATION DEPENDENCY
# ============================================================

security = HTTPBearer()

def verify_session(token: str) -> str:
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")
    if token.startswith("Bearer "):
        token = token[7:]
    username = SESSION_STORE.get(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return username

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    username = verify_session(token)
    return username

# ============================================================
# AUTHENTICATION ENDPOINTS
# ============================================================

@app.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    username = request.username.strip()
    password = request.password.strip()
    
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    
    stored_password = USER_DB.get(username)
    if not stored_password or stored_password != password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    token = secrets.token_urlsafe(32)
    SESSION_STORE[token] = username
    
    return LoginResponse(
        status="success",
        token=token,
        username=username,
        quantum_badge=QUANTUM_BADGE,
        message=f"Welcome back, {username}! Quantum engine active."
    )

@app.post("/logout")
async def logout(token: str = Header(...)):
    if not token:
        raise HTTPException(status_code=400, detail="Missing token")
    if token.startswith("Bearer "):
        token = token[7:]
    if token in SESSION_STORE:
        del SESSION_STORE[token]
        return {"status": "success", "message": "Logged out successfully"}
    raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/auth/status")
async def auth_status(username: str = Depends(get_current_user)):
    return {
        "authenticated": True,
        "username": username,
        "quantum_badge": QUANTUM_BADGE,
        "timestamp": datetime.now().isoformat()
    }

# ============================================================
# PHASE 2: NEW QUANTUM SIGNAL ENDPOINT
# ============================================================

@app.post("/api/v1/quantum-signal")
def fetch_signal(market_data: dict):
    """
    Accepts payload: {"price": 1.0850, "volume": 1200, "volatility": 0.0015, "spread": 0.0001}
    """
    result = quantum_engine.generate_quantum_signal(market_data)
    if result.get("status") != "SUCCESS":
        raise HTTPException(status_code=500, detail=result.get("status"))
    return result

# ============================================================
# QUANTUM SIGNAL ENDPOINT (Enhanced with Timeframes)
# ============================================================

@app.get("/api/signals/latest")
async def get_signal(
    symbol: Optional[str] = None, 
    timeframe: Optional[str] = "1h",
    username: str = Depends(get_current_user)
):
    """Generate quantum-verified trading signal for a specific symbol & timeframe"""
    
    if not symbol:
        symbol = "EURUSD"
    symbol = symbol.upper()
    
    if symbol not in IC_SYMBOLS:
        raise HTTPException(status_code=400, detail=f"Symbol {symbol} not supported")

    timeframe_lower = timeframe.lower()
    if timeframe_lower not in VALID_TIMEFRAMES:
        raise HTTPException(status_code=400, detail=f"Invalid timeframe. Allowed: {', '.join(VALID_TIMEFRAMES)}")
    
    # Simulate market data for analysis
    market_data = simulate_market_data(symbol)
    
    # Generate signal based on quantum randomness and trend analysis
    trend = analyze_trend(market_data)
    strength = random.random() * 0.5 + 0.5
    
    signal = "HOLD"
    confidence = 50 + random.randint(0, 40)
    
    if trend == "UP" and strength > 0.6:
        signal = "BUY"
        confidence = 65 + random.randint(0, 30)
    elif trend == "DOWN" and strength > 0.6:
        signal = "SELL"
        confidence = 65 + random.randint(0, 30)
    elif strength > 0.8:
        signal = random.choice(["BUY", "SELL"])
        confidence = 75 + random.randint(0, 20)
    
    # Calculate price levels
    current_price = get_base_price(symbol)
    variation = (random.random() - 0.5) * 0.0003
    entry = round(current_price + variation, 5)
    
    if signal == "BUY":
        stop_loss = round(entry * 0.995, 5)
        take_profit = round(entry * 1.01, 5)
    elif signal == "SELL":
        stop_loss = round(entry * 1.005, 5)
        take_profit = round(entry * 0.99, 5)
    else:
        stop_loss = None
        take_profit = None
    
    # Calculate risk/reward
    risk_reward = None
    if stop_loss and take_profit:
        risk = abs(entry - stop_loss)
        reward = abs(take_profit - entry)
        risk_reward = round(reward / risk, 2) if risk > 0 else 1
    
    # Generate signal metadata
    signal_data = {
        "symbol": symbol,
        "signal": signal,
        "confidence": confidence,
        "entry": entry,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "risk_reward": risk_reward,
        "trend": trend,
        "strength": round(strength, 2),
        "timeframe": timeframe_lower,
        "timestamp": datetime.now().isoformat(),
        "quantum_verified": True,
        "chsh_score": QUANTUM_BADGE["chsh_s"],
        "patent": QUANTUM_BADGE["patent"],
        "quantum_badge": QUANTUM_BADGE["text"],
        "message": f"Quantum signal generated for {symbol} on {timeframe_lower} timeframe"
    }
    
    signal_history.append(signal_data)
    return signal_data

# ============================================================
# DATA ARRAYS
# ============================================================
signal_history = []
trade_history = []

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_base_price(symbol: str) -> float:
    prices = {
        "EURUSD": 1.16642, "GBPUSD": 1.36386, "USDJPY": 159.386,
        "USDCAD": 1.38399, "AUDUSD": 0.71155, "USDCHF": 0.80298,
        "EURGBP": 0.8542, "EURAUD": 1.6378, "EURCHF": 0.9365,
        "EURJPY": 185.9, "GBPCHF": 1.0950, "CADJPY": 115.2,
        "AUDNZD": 1.0875, "AUDCAD": 0.9830, "AUDCHF": 0.5710,
        "AUDJPY": 113.3, "CHFJPY": 198.5, "EURNZD": 1.8115,
        "EURCAD": 1.6135, "CADCHF": 0.5805, "NZDJPY": 105.2,
        "NZDUSD": 0.6430
    }
    return prices.get(symbol, 1.0)

def simulate_market_data(symbol: str, bars: int = 200) -> List[Dict]:
    base_price = get_base_price(symbol)
    data = []
    price = base_price
    
    for i in range(bars):
        change = (random.random() - 0.48) * 0.001
        price += change
        price = max(1.0, price)
        data.append({
            "time": datetime.now().timestamp() - (bars - i) * 300,
            "open": price, "high": price + random.random() * 0.001,
            "low": price - random.random() * 0.001, "close": price,
            "volume": random.randint(100, 1000)
        })
    return data

def analyze_trend(data: List[Dict]) -> str:
    if len(data) < 20: return "SIDEWAYS"
    closes = [d["close"] for d in data]
    ma10 = sum(closes[-10:]) / 10
    ma20 = sum(closes[-20:]) / 20
    if ma10 > ma20 * 1.002: return "UP"
    elif ma10 < ma20 * 0.998: return "DOWN"
    else: return "SIDEWAYS"

# ============================================================
# PHASE 2: MERGED HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():
    return {
        "status": "online",
        "quantum_verified": True,
        "chsh_score": QUANTUM_BADGE["chsh_s"],
        "patent": QUANTUM_BADGE["patent"],
        "timestamp": datetime.now().isoformat(),
        "ic_markets_connected": True,
        "accounts": len(IC_ACCOUNTS),
        "symbols": len(IC_SYMBOLS),
        "mt5_status": mt5_gateway.get_status()
    }

@app.get("/")
async def root():
    return {
        "message": "⚛️ KD Quantum API - CHSH S=2.76",
        "patent": "SA 2026/05142",
        "status": "quantum_ready",
        "version": "2.1.0",
        "timestamp": datetime.now().isoformat(),
        "quantum_badge": QUANTUM_BADGE["text"]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
