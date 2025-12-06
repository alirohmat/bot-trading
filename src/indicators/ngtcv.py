from typing import Dict, Tuple, List
from config import NGTCV_WEIGHTS

def calculate_average_volume(historical_volumes: List[float], period: int = 20) -> float:
    """
    Menghitung rata-rata volume historis
    
    Args:
        historical_volumes: Daftar volume historis
        period: Periode untuk menghitung rata-rata (default 20)
        
    Returns:
        Rata-rata volume dari periode terakhir
    """
    if not historical_volumes:
        return 1000.0  # Default fallback
    
    # Ambil volume dari periode terakhir
    recent_volumes = historical_volumes[-period:] if len(historical_volumes) >= period else historical_volumes
    
    if not recent_volumes:
        return 1000.0  # Default fallback
    
    return sum(recent_volumes) / len(recent_volumes)

def calculate_ngtCV(candle: Dict) -> Tuple[float, float, float, float]:
    """
    Menghitung indikator ngtCV yang ditingkatkan dengan normalisasi dan arah
    
    Args:
        candle: Dictionary yang berisi data OHLCV, termasuk 'historical_volumes' untuk perhitungan referensi volume dinamis
        
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
    # Ambil data volume historis dari parameter tambahan
    historical_volumes = candle.get('historical_volumes', [])
    
    # Hitung body candle
    body_size = float(abs(close_price - open_price))
    
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
        wick_ratio = float(total_wick / total_range)
    else:
        body_ratio = 0.0
        wick_ratio = 0.0
        
    # Volume factor - sekarang dibandingkan dengan rata-rata volume historis sebagai referensi dinamis
    if volume > 0:
        # Kita gunakan volume sebagai faktor normalisasi terhadap rata-rata volume historis
        avg_volume_reference = calculate_average_volume(historical_volumes)
        volume_factor = volume / avg_volume_reference if avg_volume_reference > 0 else 1.0
    else:
        volume_factor = 1.0  # Default jika volume tidak tersedia
    
    # Hitung ngtCV
    # Komponen body memberikan arah (positif/negatif)
    # Komponen wick biasanya mengurangi kekuatan tren (rejection)
    # Komponen volume memperkuat sinyal sesuai dengan bobot yang ditentukan
    
    # Perhitungan yang memasukkan volume_factor ke dalam rumus
    ngtcv = (
        (body_ratio * candle_direction * NGTCV_WEIGHTS['body']) +
        (wick_ratio * -1 * abs(NGTCV_WEIGHTS['wick'])) +  # Wick selalu mengurangi confidence
        (volume_factor * NGTCV_WEIGHTS['volume'])  # Volume sebagai faktor konfirmasi
    )
    
    # Pastikan hasil tetap dalam range [-1.0, 1.0]
    ngtcv = max(-1.0, min(1.0, ngtcv))
    
    return ngtcv, body_size, wick_ratio, volume_factor
