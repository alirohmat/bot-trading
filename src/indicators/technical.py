import numpy as np
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

def calculate_ema(prices: List[float], period: int) -> float:
    """
    Calculate Exponential Moving Average (EMA)
    """
    if len(prices) < period:
        return prices[-1] if prices else 0.0
        
    multiplier = 2 / (period + 1)
    ema = prices[0]
    
    # Simple EMA calculation loop
    # For production, pandas ewm is more efficient but we use pure python/numpy here
    # to keep dependencies minimal
    for price in prices[1:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))
        
    return float(ema)

def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9):
    """
    Calculate MACD (Moving Average Convergence Divergence)
    Returns: (macd_line, signal_line, histogram)
    """
    if len(prices) < slow:
        return 0.0, 0.0, 0.0
    
    # Calculate the full EMA series for both fast and slow EMAs
    # Using a more efficient approach
    multiplier_fast = 2 / (fast + 1)
    multiplier_slow = 2 / (slow + 1)
    multiplier_signal = 2 / (signal + 1)
    
    # Calculate EMAs step by step for the entire series
    # Start with simple moving average as initial value
    if len(prices) >= slow:
        # Initialize EMAs with SMAs
        ema_fast = sum(prices[slow-fast:slow]) / fast  # SMA for fast EMA initialization
        ema_slow = sum(prices[:slow]) / slow          # SMA for slow EMA initialization
    else:
        # If we don't have enough data for slow EMA, use the last price
        ema_fast = ema_slow = prices[-1] if prices else 0.0
    
    # Calculate EMAs for the entire series up to the last value
    for i, price in enumerate(prices[slow:], slow):
        ema_fast = (price * multiplier_fast) + (ema_fast * (1 - multiplier_fast))
        ema_slow = (price * multiplier_slow) + (ema_slow * (1 - multiplier_slow))

    # Calculate MACD line
    macd_line = ema_fast - ema_slow
    
    # Calculate signal line (EMA of MACD line)
    # To properly calculate signal line, we need historical MACD values
    # Let's recalculate the series to get the complete MACD history
    if len(prices) >= slow + signal:
        # Calculate the full EMA series to get MACD history
        ema_fast_series = []
        ema_slow_series = []
        
        # Initialize EMAs
        if len(prices) >= slow:
            initial_ema_fast = sum(prices[slow-fast:slow]) / fast
            initial_ema_slow = sum(prices[:slow]) / slow
        else:
            initial_ema_fast = initial_ema_slow = prices[-1] if prices else 0.0
            
        # Calculate EMA series for each point
        for i, price in enumerate(prices):
            if i == 0:
                # Initialize with SMA if we have enough data, otherwise with price
                if len(prices) >= slow:
                    ema_fast_val = initial_ema_fast if i >= fast-1 else price
                    ema_slow_val = initial_ema_slow if i >= slow-1 else price
                else:
                    ema_fast_val = ema_slow_val = price
            else:
                # Apply EMA formula after we have enough data points
                if i >= fast:
                    ema_fast_val = (price * multiplier_fast) + (ema_fast_prev * (1 - multiplier_fast))
                else:
                    ema_fast_val = price  # Use price until we have enough data
                    
                if i >= slow:
                    ema_slow_val = (price * multiplier_slow) + (ema_slow_prev * (1 - multiplier_slow))
                else:
                    ema_slow_val = price  # Use price until we have enough data
            
            ema_fast_series.append(ema_fast_val)
            ema_slow_series.append(ema_slow_val)
            
            # Store previous values for next iteration
            ema_fast_prev = ema_fast_val
            ema_slow_prev = ema_slow_val
        
        # Calculate MACD line history
        macd_history = [fast_ema - slow_ema for fast_ema, slow_ema in
                       zip(ema_fast_series[slow-1:], ema_slow_series)]
        
        # Calculate signal line (EMA of MACD line)
        # Initialize signal line with SMA of first 'signal' MACD values
        signal_line = sum(macd_history[:signal]) / signal
        
        # Apply EMA formula to subsequent values
        for macd_val in macd_history[signal:]:
            signal_line = (macd_val * multiplier_signal) + (signal_line * (1 - multiplier_signal))
    else:
        # If we don't have enough data, initialize signal line to same as MACD line
        signal_line = macd_line

    # Calculate histogram (difference between MACD line and signal line)
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram
