from typing import List, Dict, Tuple, Optional
from src.indicators.ngtcv import calculate_ngtCV
from src.indicators.technical import calculate_rsi, calculate_ema, calculate_ema_multiple, calculate_macd, calculate_adx
from src.indicators.atr import calculate_atr
from src.indicators.support_resistance import is_near_support_resistance
from config import THRESHOLD_MULTIPLIER, RSI_OVERBOUGHT, RSI_OVERSOLD, EMA_SHORT_PERIOD, EMA_LONG_PERIOD, EMA_TREND_PERIOD, RISK_MANAGEMENT

def analyze_market(data: List[Dict], higher_timeframe_data: List[Dict] = None) -> Tuple[str, float, Dict]:
    """
    Menganalisis pasar menggunakan multi-indicator approach dengan filter tren jangka panjang
    Returns: trend, confidence, indicators_dict
    """
    if len(data) < max(30, EMA_TREND_PERIOD):  # Ensure we have enough data for EMA 20
        return "NEUTRAL", 0.0, {}

    # Extract prices
    closes = [c['close'] for c in data]
    highs = [c['high'] for c in data]
    lows = [c['low'] for c in data]

    # 1. Calculate ADX to filter choppy markets
    adx = calculate_adx(highs, lows, closes)
    if adx < 20:  # Market is choppy/sideways, don't trade
        return "NEUTRAL", 0.0, {
            'rsi': calculate_rsi(closes),
            'adx': adx,
            'comment': 'Market too choppy, ADX < 20'
        }

    # 2. Calculate True Multi-timeframe Trend Filter (EMA 50 on higher timeframe)
    # If higher_timeframe_data is provided, use it for trend filter
    if higher_timeframe_data and len(higher_timeframe_data) >= 50:
        higher_closes = [c['close'] for c in higher_timeframe_data]
        ema_trend_long = calculate_ema(higher_closes, 50)  # EMA 50 on higher timeframe
        current_price = closes[-1]
        trend_filter = "BULLISH" if current_price > ema_trend_long else "BEARISH"
    else:
        # Fallback to current timeframe if no higher timeframe data available
        ema_trend_long = calculate_ema(closes, EMA_TREND_PERIOD)
        current_price = closes[-1]
        trend_filter = "BULLISH" if current_price > ema_trend_long else "BEARISH"

    # 3. Calculate Position relative to Support/Resistance levels
    sr_position = is_near_support_resistance(current_price, data)

    # 4. Calculate RSI
    rsi = calculate_rsi(closes)

    # 5. Calculate EMAs (short and long term)
    ema_short = calculate_ema(closes, EMA_SHORT_PERIOD)
    ema_long = calculate_ema(closes, EMA_LONG_PERIOD)
    ema_cross_trend = "BULLISH" if ema_short > ema_long else "BEARISH"

    # 6. Calculate MACD for additional momentum confirmation
    macd_line, signal_line, macd_histogram = calculate_macd(closes)
    macd_trend = "BULLISH" if macd_line > signal_line else "BEARISH"

    # 7. Calculate ngtCV (Average of last 3 candles)
    recent_candles = data[-3:]
    ngtcv_sum = 0
    for candle in recent_candles:
        val, _, _, _ = calculate_ngtCV(candle)
        ngtcv_sum += val
    avg_ngtcv = ngtcv_sum / 3

    # 8. Calculate ATR for dynamic risk management
    atr_value = calculate_atr(data)

    # 9. Check for bullish/bearish engulfing pattern
    is_bullish_engulfing = False
    is_bearish_engulfing = False
    if len(data) >= 2:
        current_candle = data[-1]
        prev_candle = data[-2]

        # Bullish engulfing: current close > current open AND current body engulfs previous body
        current_body = abs(current_candle['close'] - current_candle['open'])
        prev_body = abs(prev_candle['close'] - prev_candle['open'])

        if current_candle['close'] > current_candle['open']:  # Current candle is bullish
            if (current_candle['close'] > prev_candle['open'] and 
                current_candle['open'] < prev_candle['close']):
                is_bullish_engulfing = True

        if current_candle['close'] < current_candle['open']:  # Current candle is bearish
            if (current_candle['open'] > prev_candle['close'] and 
                current_candle['close'] < prev_candle['open']):
                is_bearish_engulfing = True

    # Combine Signals with Trend Filter Applied
    score = 0

    # Apply Trend Filter First - Only allow signals in direction of long-term trend
    if trend_filter == "BULLISH":
        # Only allow BUY signals in uptrend
        if rsi < RSI_OVERSOLD and is_bullish_engulfing:  # Oversold in uptrend + bullish engulfing = potential buy on dip
            score += 3  # Higher weight for trend-aligned signal with price action confirmation
        elif rsi < RSI_OVERSOLD:  # Oversold in uptrend = potential buy on dip (but without price action)
            score += 2 # Higher weight for trend-aligned signal
        elif rsi > RSI_OVERBOUGHT:  # Overbought in uptrend = potential reversal
            score -= 0.5  # Lower weight against trend
    elif trend_filter == "BEARISH":
        # Only allow SELL signals in downtrend
        if rsi > RSI_OVERBOUGHT and is_bearish_engulfing:  # Overbought in downtrend + bearish engulfing = potential sell on rally
            score -= 3 # Higher weight for trend-aligned signal with price action confirmation
        elif rsi > RSI_OVERBOUGHT:  # Overbought in downtrend = potential sell on rally (but without price action)
            score -= 2 # Higher weight for trend-aligned signal
        elif rsi < RSI_OVERSOLD:  # Oversold in downtrend = potential reversal
            score += 0.5  # Lower weight against trend

    # Additional Multi-timeframe analysis (suggested in revisi.md)
    # Check for momentum confirmation using additional indicators
    if len(closes) >= 50:  # Ensure we have enough data
        ema_50 = calculate_ema(closes, 50)
        if current_price > ema_50 and trend_filter == "BULLISH":
            score += 0.5  # Additional confirmation for bullish trend
        elif current_price < ema_50 and trend_filter == "BEARISH":
            score -= 0.5  # Additional confirmation for bearish trend

    # EMA Cross Confirmation (only when aligned with trend filter)
    if ema_cross_trend == trend_filter:
        if ema_cross_trend == "BULLISH":
            score += 1
        else:
            score -= 1

    # MACD Confirmation (only when aligned with trend filter)
    if macd_trend == trend_filter:
        if macd_trend == "BULLISH":
            score += 0.8  # Slightly lower weight than EMA cross
        else:
            score -= 0.8

    # ngtCV Scoring (only when aligned with trend filter)
    if trend_filter == "BULLISH":
        if avg_ngtcv > 0.1:  # Positive volume confirmation in uptrend
            score += 0.5
        elif avg_ngtcv < -0.1:  # Negative volume confirmation in uptrend
            score -= 0.5
    elif trend_filter == "BEARISH":
        if avg_ngtcv < -0.1:  # Negative volume confirmation in downtrend
            score -= 0.5
        elif avg_ngtcv > 0.1:  # Positive volume confirmation in downtrend
            score += 0.5

    # Support/Resistance Scoring (Point E dari revisi.md)
    # Prioritaskan sinyal di dekat level kunci daripada di tengah-tengah pasar
    if sr_position == "NEAR_SUPPORT" and trend_filter == "BULLISH":
        # Sinyal BUY di dekat support dalam tren naik = probabilitas tinggi
        score += 1.0
    elif sr_position == "NEAR_RESISTANCE" and trend_filter == "BEARISH":
        # Sinyal SELL di dekat resistance dalam tren turun = probabilitas tinggi
        score -= 1.0
    elif sr_position == "AWAY_FROM_LEVELS":
        # Sinyal di tengah-tengah (no man's land) = kurangi probabilitas
        score -= 0.5

    # Determine Final Signal
    max_possible_score = 7.8  # Maximum possible score based on our updated scoring system (increased due to engulfing pattern)
    confidence = abs(score) / max_possible_score  # Normalize to 0-1

    trend = "NEUTRAL"
    if score >= 1.5 and confidence >= RISK_MANAGEMENT['min_confidence']:
        trend = "BULLISH"
    elif score <= -1.5 and confidence >= RISK_MANAGEMENT['min_confidence']:
        trend = "BEARISH"

    indicators = {
        'rsi': rsi,
        'ema_short': ema_short,
        'ema_long': ema_long,
        'ema_trend': ema_cross_trend,
        'ema_trend_long': ema_trend_long,
        'trend_filter': trend_filter,
        'sr_position': sr_position,
        'ngtcv': avg_ngtcv,
        'atr': atr_value,
        'macd_line': macd_line,
        'signal_line': signal_line,
        'macd_histogram': macd_histogram,
        'adx': adx,
        'is_bullish_engulfing': is_bullish_engulfing,
        'is_bearish_engulfing': is_bearish_engulfing
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

def calculate_atr_based_targets(entry_price: float, atr_value: float) -> Tuple[float, float]:
    """
    Calculate dynamic stop loss and take profit levels based on ATR
    Returns: (stop_loss, take_profit)
    """
    sl_multiplier = RISK_MANAGEMENT['atr_multiplier_sl']
    tp_multiplier = RISK_MANAGEMENT['atr_multiplier_tp']

    stop_loss = entry_price - (sl_multiplier * atr_value) if entry_price > 0 else 0
    take_profit = entry_price + (tp_multiplier * atr_value) if entry_price > 0 else 0

    return stop_loss, take_profit

def evaluate_prediction(previous_candle: Dict, current_candle: Dict, prediction: Optional[Tuple[str, float]], atr_value: float = None) -> Tuple[bool, float]:
    """
    Evaluasi prediksi dengan threshold persentase dan manajemen risiko berbasis ATR
    """
    if not prediction or prediction[0] == "HOLD":
        return None, 0.0

    pred_signal, _ = prediction
    previous_close = previous_candle['close']
    current_close = current_candle['close']

    # Jika ATR tersedia, gunakan manajemen risiko berbasis ATR
    if atr_value is not None:
        stop_loss, take_profit = calculate_atr_based_targets(previous_close, atr_value)

        # Evaluasi berdasarkan apakah harga menyentuh SL atau TP sebelum akhir periode
        if pred_signal == "BUY":
            if current_close <= stop_loss:
                return False, abs((current_close - previous_close) / previous_close * 100)  # Loss
            elif current_close >= take_profit:
                return True, abs((current_close - previous_close) / previous_close * 100)   # Profit
        elif pred_signal == "SELL":
            if current_close >= stop_loss:
                return False, abs((current_close - previous_close) / previous_close * 100)  # Loss
            elif current_close <= take_profit:
                return True, abs((current_close - previous_close) / previous_close * 100)   # Profit

    # Jika tidak menggunakan manajemen risiko ATR, gunakan metode sebelumnya
    price_change_pct = ((current_close - previous_close) / previous_close) * 100

    # Hanya evaluate jika ada perubahan signifikan (> 0.1%)
    # Menggunakan threshold kecil untuk simulasi 15m
    if abs(price_change_pct) < 0.1:
        return None, 0.0

    actual_direction = "BUY" if price_change_pct > 0 else "SELL"

    is_correct = (pred_signal == actual_direction)

    return is_correct, abs(price_change_pct)

def dynamic_breakeven(entry_price: float, current_price: float, initial_stop_loss: float, 
                     breakeven_threshold: float = 0.01) -> Tuple[float, str]:
    """
    Implementasi dynamic breakeven untuk proteksi profit
    Jika harga sudah bergerak profit sebesar threshold, geser stop loss ke harga entry

    Args:
        entry_price: Harga entry posisi
        current_price: Harga saat ini
        initial_stop_loss: Stop loss awal
        breakeven_threshold: Threshold profit untuk mengaktifkan breakeven (default 1%)

    Returns:
        Tuple dari (new_stop_loss, status_breakeven)
    """
    if entry_price <= 0 or current_price <= 0:
        return initial_stop_loss, "INVALID_PRICE"

    # Hitung profit yang telah dicapai
    profit_pct = abs((current_price - entry_price) / entry_price)

    # Jika profit sudah mencapai threshold, geser SL ke harga entry
    if profit_pct >= breakeven_threshold:
        return entry_price, "BREAKEVEN_ACTIVATED"
    else:
        return initial_stop_loss, "BREAKEVEN_NOT_ACTIVATED"

def enhanced_market_analysis(data: List[Dict], higher_timeframe_data: List[Dict] = None) -> Tuple[str, float, Dict]:
    """
    Fungsi utama yang menggabungkan semua perubahan dari revisi.md
    """
    # Panggil fungsi analyze_market yang telah diperbarui
    trend, confidence, indicators = analyze_market(data, higher_timeframe_data)

    # Jika pasar terlalu choppy (ADX < 20), kembalikan NEUTRAL
    if 'adx' in indicators and indicators['adx'] < 20:
        return "NEUTRAL", 0.0, indicators

    # Tambahkan informasi tambahan ke dalam indikator
    enhanced_indicators = indicators.copy()
    enhanced_indicators['analysis_version'] = 'enhanced_with_adx_and_tmf'

    return trend, confidence, enhanced_indicators
