from typing import List, Dict, Tuple, Optional
from src.indicators.ngtcv import calculate_ngtCV
from src.indicators.technical import calculate_rsi, calculate_ema
from config import THRESHOLD_MULTIPLIER, RSI_OVERBOUGHT, RSI_OVERSOLD, EMA_SHORT_PERIOD, EMA_LONG_PERIOD, RISK_MANAGEMENT

def analyze_market(data: List[Dict]) -> Tuple[str, float, Dict]:
    """
    Menganalisis pasar menggunakan multi-indicator approach
    Returns: trend, confidence, indicators_dict
    """
    if len(data) < 30:
        return "NEUTRAL", 0.0, {}
    
    # Extract prices
    closes = [c['close'] for c in data]
    
    # 1. Calculate RSI
    rsi = calculate_rsi(closes)
    
    # 2. Calculate EMAs
    ema_short = calculate_ema(closes, EMA_SHORT_PERIOD)
    ema_long = calculate_ema(closes, EMA_LONG_PERIOD)
    ema_trend = "BULLISH" if ema_short > ema_long else "BEARISH"
    
    # 3. Calculate ngtCV (Average of last 3 candles)
    recent_candles = data[-3:]
    ngtcv_sum = 0
    for candle in recent_candles:
        val, _, _, _ = calculate_ngtCV(candle)
        ngtcv_sum += val
    avg_ngtcv = ngtcv_sum / 3
    
    # Combine Signals
    score = 0
    
    # RSI Scoring
    if rsi < RSI_OVERSOLD:
        score += 1  # Potential Buy
    elif rsi > RSI_OVERBOUGHT:
        score -= 1  # Potential Sell
        
    # EMA Scoring
    if ema_trend == "BULLISH":
        score += 1
    else:
        score -= 1
        
    # ngtCV Scoring
    if avg_ngtcv > 0.1:
        score += 1
    elif avg_ngtcv < -0.1:
        score -= 1
        
    # Determine Final Signal
    confidence = abs(score) / 3.0  # Normalize to 0-1
    
    trend = "NEUTRAL"
    if score >= 2 and confidence >= RISK_MANAGEMENT['min_confidence']:
        trend = "BULLISH"
    elif score <= -2 and confidence >= RISK_MANAGEMENT['min_confidence']:
        trend = "BEARISH"
        
    indicators = {
        'rsi': rsi,
        'ema_short': ema_short,
        'ema_long': ema_long,
        'ema_trend': ema_trend,
        'ngtcv': avg_ngtcv
    }
    
    return trend, confidence, indicators

def generate_signal(market_analysis: Tuple[str, float, Dict]) -> Tuple[str, float]:
    """
    Generate BUY/SELL signal
    """
    trend, confidence, _ = market_analysis
    
    if trend == "BULLISH":
        return "BUY", confidence
    elif trend == "BEARISH":
        return "SELL", confidence
    else:
        return "HOLD", 0.0

def evaluate_prediction(previous_candle: Dict, current_candle: Dict, prediction: Optional[Tuple[str, float]]) -> Tuple[bool, float]:
    """
    Evaluasi prediksi dengan threshold persentase
    """
    if not prediction or prediction[0] == "HOLD":
        return None, 0.0
    
    pred_signal, _ = prediction
    previous_close = previous_candle['close']
    current_close = current_candle['close']
    
    # Hitung perubahan persentase
    price_change_pct = ((current_close - previous_close) / previous_close) * 100
    
    # Hanya evaluate jika ada perubahan signifikan (> 0.1%)
    # Menggunakan threshold kecil untuk simulasi 15m
    if abs(price_change_pct) < 0.1:
        return None, 0.0
    
    actual_direction = "BUY" if price_change_pct > 0 else "SELL"
    
    is_correct = (pred_signal == actual_direction)
    
    return is_correct, abs(price_change_pct)
