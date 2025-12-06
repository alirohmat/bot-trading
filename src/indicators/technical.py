import numpy as np
import pandas as pd
from typing import List, Dict

def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """
    Calculate Relative Strength Index (RSI)
    """
    if len(prices) < period + 1:
        return 50.0
        
    # Calculate price changes
    deltas = np.diff(prices)
    
    # Separate gains and losses
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    # Calculate average gain and loss
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100.0
        
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return float(rsi)

def calculate_ema_pandas(series: pd.Series, period: int) -> float:
    """
    Calculate Exponential Moving Average using pandas (more efficient)
    """
    if len(series) == 0:
        return 0.0
    elif len(series) < period:
        # Jika data lebih sedikit dari periode, kita bisa menggunakan rata-rata
        return float(series.mean())
    else:
        ema_series = series.ewm(span=period, adjust=False).mean()
        return float(ema_series.iloc[-1])

def calculate_ema(prices: List[float], period: int) -> float:
    """
    Calculate Exponential Moving Average (EMA)
    """
    if not prices:
        return 0.0
    elif len(prices) < period:
        # Jika data lebih sedikit dari periode, kita bisa menggunakan rata-rata
        return sum(prices) / len(prices)
    
    # Using pandas for more efficient calculation
    series = pd.Series(prices)
    return calculate_ema_pandas(series, period)

def calculate_ema_multiple(prices: List[float], periods: List[int]) -> Dict[int, float]:
    """
    Calculate multiple EMAs at once for efficiency
    Returns a dictionary with period as key and EMA value as value
    """
    if not prices:
        return {period: 0.0 for period in periods}
    
    import pandas as pd
    series = pd.Series(prices)
    
    result = {}
    for period in periods:
        if len(prices) < period:
            # If data is less than period, use average
            result[period] = sum(prices) / len(prices)
        else:
            ema_series = series.ewm(span=period, adjust=False).mean()
            result[period] = float(ema_series.iloc[-1])
    
    return result

def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9):
    """
    Calculate MACD (Moving Average Convergence Divergence) using pandas for efficiency
    Returns: (macd_line, signal_line, histogram)
    """
    if len(prices) < slow:
        return 0.0, 0.0, 0.0
    
    # Convert to pandas Series for vectorized operations
    series = pd.Series(prices)
    
    # Calculate EMAs using pandas ewm function (much more efficient)
    ema_fast = series.ewm(span=fast, adjust=False).mean().iloc[-1]
    ema_slow = series.ewm(span=slow, adjust=False).mean().iloc[-1]
    
    # Calculate MACD line
    macd_line = ema_fast - ema_slow
    
    # For signal line, we need the historical MACD values
    if len(prices) >= slow + signal:
        # Calculate the complete history of MACD values
        ema_fast_series = series.ewm(span=fast, adjust=False).mean()
        ema_slow_series = series.ewm(span=slow, adjust=False).mean()
        macd_series = ema_fast_series - ema_slow_series
        
        # Get the last 'signal' number of MACD values to calculate the signal line
        recent_macd_values = macd_series.iloc[-signal:]
        signal_line = recent_macd_values.ewm(span=signal, adjust=False).mean().iloc[-1]
    else:
        # If we don't have enough data, initialize signal line to same as MACD line
        signal_line = macd_line

    # Calculate histogram (difference between MACD line and signal line)
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def calculate_adx(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    """
    Calculate Average Directional Index (ADX)
    """
    if len(highs) < period + 1:
        return 25.0  # Return neutral value if not enough data
    
    # Calculate True Range (TR)
    tr_values = []
    for i in range(1, len(highs)):
        tr = max(
            highs[i] - lows[i],  # High - Low
            abs(highs[i] - closes[i-1]),  # High - Previous Close
            abs(lows[i] - closes[i-1])  # Low - Previous Close
        )
        tr_values.append(tr)
    
    # Calculate Directional Movement (+DM and -DM)
    plus_dm = []
    minus_dm = []
    for i in range(1, len(highs)):
        up_move = highs[i] - highs[i-1]
        down_move = lows[i-1] - lows[i]
        
        if up_move > down_move and up_move > 0:
            plus_dm.append(up_move)
        else:
            plus_dm.append(0)
        
        if down_move > up_move and down_move > 0:
            minus_dm.append(down_move)
        else:
            minus_dm.append(0)
    
    # Smooth the values using Wilder's method
    smoothed_tr = [sum(tr_values[:period])]
    smoothed_plus_dm = [sum(plus_dm[:period])]
    smoothed_minus_dm = [sum(minus_dm[:period])]
    
    for i in range(period, len(tr_values)):
        smoothed_tr.append(smoothed_tr[-1] - (smoothed_tr[-1] / period) + tr_values[i])
        smoothed_plus_dm.append(
            smoothed_plus_dm[-1] - (smoothed_plus_dm[-1] / period) + plus_dm[i]
        )
        smoothed_minus_dm.append(
            smoothed_minus_dm[-1] - (smoothed_minus_dm[-1] / period) + minus_dm[i]
        )
    
    # Calculate Directional Indicators (+DI and -DI)
    plus_di = [(smoothed_plus_dm[i] / smoothed_tr[i]) * 100 if smoothed_tr[i] != 0 else 0
               for i in range(len(smoothed_tr))]
    minus_di = [(smoothed_minus_dm[i] / smoothed_tr[i]) * 100 if smoothed_tr[i] != 0 else 0
                for i in range(len(smoothed_tr))]
    
    # Calculate Directional Movement Index (DX)
    dx_values = []
    for i in range(len(plus_di)):
        total_di = plus_di[i] + minus_di[i]
        dx = (abs(plus_di[i] - minus_di[i]) / total_di) * 100 if total_di != 0 else 0
        dx_values.append(dx)
    
    # Calculate ADX (average of DX)
    if len(dx_values) >= period:
        adx = sum(dx_values[-period:]) / period
        return float(adx)
    else:
        return 25.0  # Return neutral value if not enough data
