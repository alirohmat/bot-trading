import numpy as np
import pandas as pd
from typing import List

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
