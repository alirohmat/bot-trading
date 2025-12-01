from typing import Dict, Tuple
from config import NGTCV_WEIGHTS

def calculate_ngtCV(candle: Dict) -> Tuple[float, float, float, float]:
    """
    Menghitung indikator ngtCV yang ditingkatkan dengan normalisasi dan arah
    
    Returns:
        ngtcv: Nilai indikator (-1.0 to 1.0)
        body_size: Ukuran body candle
        wick_ratio: Rasio wick terhadap range total
        volume_factor: Volume normalized
    """
    open_price = candle['open']
    close_price = candle['close']
    high_price = candle['high']
    low_price = candle['low']
    volume = candle['volume']
    
    # Hitung body candle
    body_size = abs(close_price - open_price)
    
    # Tentukan arah candle (1 untuk bullish, -1 untuk bearish)
    candle_direction = 1 if close_price >= open_price else -1
    
    # Hitung shadows
    upper_shadow = high_price - max(open_price, close_price)
    lower_shadow = min(open_price, close_price) - low_price
    total_wick = upper_shadow + lower_shadow
    
    # Hitung total range
    total_range = high_price - low_price
    
    # Normalisasi (hindari pembagian dengan nol)
    if total_range > 0:
        body_ratio = body_size / total_range
        wick_ratio = total_wick / total_range
    else:
        body_ratio = 0
        wick_ratio = 0
        
    # Volume factor (sebaiknya dinormalisasi terhadap rata-rata, tapi di sini kita pakai raw dulu)
    # Untuk perbaikan lebih lanjut, kita perlu passing average volume
    volume_factor = volume 
    
    # Hitung ngtCV
    # Komponen body memberikan arah (positif/negatif)
    # Komponen wick biasanya mengurangi kekuatan tren (rejection)
    # Komponen volume memperkuat sinyal
    
    # Simplified calculation for this version
    ngtcv = (
        (body_ratio * candle_direction * NGTCV_WEIGHTS['body']) + 
        (wick_ratio * -1 * abs(NGTCV_WEIGHTS['wick'])) # Wick selalu mengurangi confidence
    )
    
    return ngtcv, body_size, wick_ratio, volume_factor
