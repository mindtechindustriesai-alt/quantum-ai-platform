# app/services/metatrader_service.py
# Add this at the top:

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    mt5 = None
    print("⚠️ MetaTrader5 not available (Linux environment)")

# Then use MT5_AVAILABLE checks throughout the code
