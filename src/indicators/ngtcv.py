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
        
    # Volume factor - untuk implementasi lengkap, ini seharusnya dibandingkan dengan rata-rata volume sebelumnya
    # Namun untuk saat ini, kita tetap mengembalikan volume_factor agar kompatibel dengan fungsi lain
    # Dalam implementasi yang lebih lengkap, parameter tambahan diperlukan untuk menyediakan rata-rata volume
    if volume > 0:
        # Kita gunakan volume sebagai faktor normalisasi terhadap nilai tetap untuk saat ini
        # Dalam implementasi sebenarnya, ini harus dibandingkan dengan rata-rata volume sebelumnya
        avg_volume_reference = 1000  # Nilai referensi - dalam praktik sebenarnya ini harus dihitung dari data sebelumnya
        volume_factor = volume / avg_volume_reference
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
