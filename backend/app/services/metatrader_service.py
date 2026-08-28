"""
MetaTrader 5 Integration Service
Live trading data and execution
CHSH S=2.76 · SA 2026/05142
"""

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class MetaTraderService:
    def __init__(self):
        self.connected = False
        self.account_id = None
        self.symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'AUDUSD']
        self.timeframes = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
        }

    def connect(self, account_id: int, password: str, server: str) -> bool:
        """Connect to MetaTrader 5"""
        try:
            if not mt5.initialize():
                logger.error("MT5 initialize failed")
                return False

            authorized = mt5.login(
                login=account_id,
                password=password,
                server=server
            )

            if not authorized:
                logger.error(f"MT5 login failed: {mt5.last_error()}")
                return False

            self.connected = True
            self.account_id = account_id
            logger.info(f"✅ MT5 connected: {account_id} on {server}")
            return True

        except Exception as e:
            logger.error(f"MT5 connection error: {e}")
            return False

    def get_symbol_data(self, symbol: str, timeframe: str = 'H4', bars: int = 500) -> Dict:
        """Fetch OHLCV data for symbol"""
        if not self.connected:
            return {'error': 'Not connected to MT5'}

        try:
            tf = self.timeframes.get(timeframe, mt5.TIMEFRAME_H4)
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)

            if rates is None or len(rates) == 0:
                return {'error': 'No data available'}

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')

            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'data': df.to_dict('records'),
                'count': len(rates),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return {'error': str(e)}

    def get_current_price(self, symbol: str) -> Dict:
        """Get current bid/ask price"""
        if not self.connected:
            return {'error': 'Not connected'}

        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return {'error': f'No tick data for {symbol}'}

            return {
                'symbol': symbol,
                'bid': tick.bid,
                'ask': tick.ask,
                'spread': tick.ask - tick.bid,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {'error': str(e)}

    def execute_trade(self, action: str, symbol: str, volume: float,
                      stop_loss: float = None, take_profit: float = None,
                      comment: str = "Quantum Signal") -> Dict:
        """Execute a trade on MT5"""
        if not self.connected:
            return {'error': 'Not connected to MT5'}

        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return {'error': f'Symbol {symbol} not found'}

            order_type = mt5.ORDER_TYPE_BUY if action == 'BUY' else mt5.ORDER_TYPE_SELL
            price = symbol_info.ask if action == 'BUY' else symbol_info.bid

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": float(volume),
                "type": order_type,
                "price": price,
                "deviation": 20,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
                "comment": comment,
            }

            if stop_loss:
                request["sl"] = stop_loss
            if take_profit:
                request["tp"] = take_profit

            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {
                    'error': f'Order failed: {result.comment}',
                    'retcode': result.retcode
                }

            return {
                'success': True,
                'order_id': result.order,
                'volume': result.volume,
                'price': result.price,
                'symbol': symbol,
                'action': action,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return {'error': str(e)}

    def get_account_info(self) -> Dict:
        """Get account information"""
        if not self.connected:
            return {'error': 'Not connected'}

        try:
            account_info = mt5.account_info()
            if account_info is None:
                return {'error': 'Failed to get account info'}

            return {
                'balance': account_info.balance,
                'equity': account_info.equity,
                'margin': account_info.margin,
                'free_margin': account_info.margin_free,
                'margin_level': account_info.margin_level,
                'open_trades': account_info.positions_total,
                'currency': account_info.currency,
                'server': account_info.server,
                'trade_mode': account_info.trade_mode
            }

        except Exception as e:
            return {'error': str(e)}
