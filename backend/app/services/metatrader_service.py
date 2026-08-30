import sys
import logging

logger = logging.getLogger(__name__)

class MT5Gateway:
    def __init__(self):
        self.mt5 = None
        self.is_available = False
        self._initialize_bridge()

    def _initialize_bridge(self):
        try:
            if sys.platform.startswith("win"):
                import MetaTrader5 as mt5
                self.mt5 = mt5
                logger.info("Native Windows MetaTrader5 module loaded.")
            else:
                from mt5linux import MetaTrader5 as mt5
                self.mt5 = mt5
                logger.info("Linux RPyC MetaTrader5 bridge initialized.")

            if self.mt5.initialize():
                self.is_available = True
                logger.info("MT5 Connection successfully established.")
            else:
                logger.warning(f"MT5 initialization failed: {self.mt5.last_error()}")
        except Exception as e:
            logger.error(f"MetaTrader5 environment check bypassed: {e}")
            self.is_available = False

    def get_status(self):
        return {
            "platform": sys.platform,
            "mt5_connected": self.is_available
        }

mt5_gateway = MT5Gateway()
