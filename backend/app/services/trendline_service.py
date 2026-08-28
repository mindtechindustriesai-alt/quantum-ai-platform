"""
Advanced Trendline Detection
10-Day Trendline Strategy with Linear Regression
CHSH S=2.76 · SA 2026/05142
"""

import numpy as np
from sklearn.linear_model import LinearRegression
from scipy.signal import find_peaks
from typing import List, Dict, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class TrendlineService:
    def __init__(self):
        self.min_points = 3
        self.max_deviation = 0.02

    def detect_trendline(self, data: List[Dict]) -> Dict:
        """Detect trendline from OHLC data"""
        if not data or len(data) < self.min_points:
            return {'trend': 'insufficient', 'confidence': 0}

        highs = [d['high'] for d in data]
        lows = [d['low'] for d in data]
        closes = [d['close'] for d in data]
        indices = np.arange(len(data))

        high_peaks, _ = find_peaks(highs, distance=5, prominence=0.0005)
        low_peaks, _ = find_peaks([-x for x in lows], distance=5, prominence=0.0005)

        slope, intercept = self._linear_regression(indices, closes)

        if slope > 0.0001:
            trend = 'UP'
        elif slope < -0.0001:
            trend = 'DOWN'
        else:
            trend = 'SIDEWAYS'

        support = min(lows)
        resistance = max(highs)
        r_squared = self._calculate_r_squared(closes, slope, intercept)
        confidence = min(100, r_squared * 100)

        breakout = self._detect_breakout(data, support, resistance)

        return {
            'trend': trend,
            'confidence': round(confidence, 2),
            'support': support,
            'resistance': resistance,
            'slope': slope,
            'intercept': intercept,
            'breakout': breakout,
            'high_peaks': len(high_peaks),
            'low_peaks': len(low_peaks),
            'data_points': len(data)
        }

    def _linear_regression(self, x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
        model = LinearRegression()
        model.fit(x.reshape(-1, 1), y)
        return model.coef_[0], model.intercept_

    def _calculate_r_squared(self, y: np.ndarray, slope: float, intercept: float) -> float:
        x = np.arange(len(y))
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    def _detect_breakout(self, data: List[Dict], support: float, resistance: float) -> bool:
        if not data or len(data) < 2:
            return False

        last_price = data[-1]['close']
        prev_price = data[-2]['close']

        breakout_up = last_price > resistance and prev_price <= resistance
        breakout_down = last_price < support and prev_price >= support

        return breakout_up or breakout_down
