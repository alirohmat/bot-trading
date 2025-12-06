from typing import List, Dict, Tuple
import numpy as np

def find_pivot_points(data: List[Dict], period: int = 10) -> Tuple[List[float], List[float]]:
    """
    Mencari level support dan resistance sederhana berdasarkan pivot high/low
    """
    if len(data) < period * 2 + 1:
        return [], []
    
    highs = [candle['high'] for candle in data]
    lows = [candle['low'] for candle in data]
    
    pivot_supports = []
    pivot_resistances = []
    
    # Cari pivot points
    for i in range(period, len(data) - period):
        # Cek apakah ini pivot low (lowest low dalam periode)
        is_pivot_low = True
        for j in range(i - period, i + period + 1):
            if j != i and lows[j] <= lows[i]:
                is_pivot_low = False
                break
        
        # Cek apakah ini pivot high (highest high dalam periode)
        is_pivot_high = True
        for j in range(i - period, i + period + 1):
            if j != i and highs[j] >= highs[i]:
                is_pivot_high = False
                break
        
        if is_pivot_low:
            pivot_supports.append(lows[i])
        elif is_pivot_high:
            pivot_resistances.append(highs[i])
    
    return pivot_supports, pivot_resistances

def get_nearest_support_resistance(current_price: float, data: List[Dict], period: int = 10) -> Tuple[float, float]:
    """
    Mendapatkan level support dan resistance terdekat dari harga saat ini
    """
    supports, resistances = find_pivot_points(data, period)
    
    nearest_support = 0
    nearest_resistance = float('inf')
    
    # Cari support terdekat di bawah harga saat ini
    for support in supports:
        if support < current_price and support > nearest_support:
            nearest_support = support
    
    # Cari resistance terdekat di atas harga saat ini
    for resistance in resistances:
        if resistance > current_price and resistance < nearest_resistance:
            nearest_resistance = resistance
    
    # Jika tidak ditemukan, kembalikan harga saat ini
    if nearest_support == 0:
        nearest_support = current_price
    if nearest_resistance == float('inf'):
        nearest_resistance = current_price
    
    return nearest_support, nearest_resistance

def is_near_support_resistance(current_price: float, data: List[Dict], tolerance: float = 0.003) -> str:
    """
    Menentukan apakah harga saat ini dekat dengan level support/resistance
    tolerance: persentase toleransi dari harga (default 0.3%)
    """
    support, resistance = get_nearest_support_resistance(current_price, data)
    
    tolerance_amount = current_price * tolerance
    
    # Cek apakah harga saat ini dekat dengan support
    if abs(current_price - support) <= tolerance_amount:
        return "NEAR_SUPPORT"
    # Cek apakah harga saat ini dekat dengan resistance
    elif abs(current_price - resistance) <= tolerance_amount:
        return "NEAR_RESISTANCE"
    else:
        return "AWAY_FROM_LEVELS"