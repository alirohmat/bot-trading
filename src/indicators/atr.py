import numpy as np
from typing import List, Dict

def calculate_true_range(candle: Dict, prev_candle: Dict) -> float:
    """
    Calculate True Range (TR) for ATR calculation
    TR = max[(high - low), abs(high - close_prev), abs(low - close_prev)]
    """
    high = candle['high']
    low = candle['low']
    prev_close = prev_candle['close']
    
    tr1 = high - low
    tr2 = abs(high - prev_close)
    tr3 = abs(low - prev_close)
    
    true_range = max(tr1, tr2, tr3)
    return true_range

def calculate_atr(data: List[Dict], period: int = 14) -> float:
    """
    Calculate Average True Range (ATR)
    """
    if len(data) < period + 1:
        return 0.0
    
    true_ranges = []
    for i in range(1, len(data)):
        tr = calculate_true_range(data[i], data[i-1])
        true_ranges.append(tr)
    
    # Take the last 'period' values
    recent_tr = true_ranges[-period:] if len(true_ranges) >= period else true_ranges
    
    if not recent_tr:
        return 0.0
    
    atr = sum(recent_tr) / len(recent_tr)
    return atr

def calculate_atr_percent(data: List[Dict], period: int = 14) -> float:
    """
    Calculate ATR as percentage of current price
    """
    if len(data) < period + 1:
        return 0.0
    
    current_price = data[-1]['close']
    atr = calculate_atr(data, period)
    
    if current_price == 0:
        return 0.0
    
    atr_percent = (atr / current_price) * 100
    return atr_percent