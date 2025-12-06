# Laporan Analisis & Revisi Codebase (Updated)

## 1. Analisis Performa Aktual (Win Rate Stuck ~51%)

Berdasarkan analisis kode `src/strategy/signal_generator.py` dan `src/indicators/support_resistance.py`, implementasi saat ini memiliki beberapa **kelemahan fatal** yang menyebabkan win rate tidak beranjak dari 50%:

1.  **Support/Resistance "Loose"**: Toleransi deteksi support saat ini setara **2%** dari harga (`tolerance=0.02`).
    -   *Contoh*: Pada harga BTC 100,000, toleransi ini mendeteksi area 2,000 poin sebagai "Support". Ini terlalu lebar untuk timeframe 15m, menyebabkan bot sering masuk terlalu awal.
2.  **Fake Multi-Timeframe**: Kode saat ini menghitung indikator "jangka panjang" (EMA 200) menggunakan data 15m yang sama. Ini bukan *True Multi-Timeframe*. Tren 200 candle 15m hanyalah tren 2 hari, bukan tren makro.
3.  **No Volatility Filter**: Bot tetap trading saat pasar *sideways* sempit (Low ADX), di mana indikator trend-following (EMA) dan momentum (RSI) sering memberikan sinyal palsu (whipsaw).

---

## 2. 🚀 Master Plan: Menuju Win Rate > 60%

Untuk mencapai target win rate, kita harus memperketat filter secara drastis. "Less Trades, Better Quality."

### A. True Multi-Timeframe Trend (1H / 4H) ✅ **[CRITICAL]**
Jangan gunakan data 15m untuk melihat tren besar.
-   **Logika Baru**: Fetch data tambahan **interval 1H**.
-   **Aturan**:
    -   Hitung EMA 50 pada timeframe **1H**.
    -   HANYA Buy jika: `Close (15m) > EMA 50 (1H)`.
    -   HANYA Sell jika: `Close (15m) < EMA 50 (1H)`.
-   **Efek**: Filter ini jauh lebih kuat menahan posisi lawan tren daripada EMA 200 di 15m.

### B. Perbaikan Support/Resistance Tolerance
-   **Masalah**: Toleransi 2% terlalu lebar.
-   **Solusi**: Kurangi toleransi menjadi **0.2% - 0.3%**.
    -   Hanya anggap valid jika harga benar-benar menyentuh level kunci.

### C. ADX Filter (Trend Strength)
-   **Saran**: Tambahkan indikator **ADX (Average Directional Index)**.
-   **Aturan**:
    -   Jika `ADX > 25`: Market Trending -> Gunakan Strategi Follow Trend (Buy on Dip).
    -   Jika `ADX < 20`: Market Sideways -> **JANGAN TRADING** atau gunakan strategi Mean Reversion (Buy Low, Sell High, abaikan EMA).
    -   *Rekomendasi Awal*: Matikan trading saat ADX < 20 untuk menghindari chop.

### D. Entry Trigger: Bullish/Bearish Engulfing
-   **Masalah**: Saat ini bot langsung Buy saat RSI < 30. Seringkali harga lanjut longsor (RSI menjadi 20, 15...).
-   **Solusi**: Tunggu **Konfirmasi Candle**.
    -   Sinyal: (`RSI < 30`) + (`Close > Open` / Candle Hijau) + (`Close > High candle sebelumnya`).
    -   Artinya kita tidak menangkap pisau jatuh, tapi menunggu pantulan pertama.

### E. Dynamic Breakeven (Protect Profits)
-   **Saran**: Jika harga sudah bergerak profit +1% (atau +1R), geser Stop Loss ke harga Entry.
-   **Efek**: Mengubah trade yang "hampir profit lalu balik arah" menjadi BEP (Break Even Point), bukan Loss. Ini menjaga Win Rate (atau setidaknya Loss Rate).

---

## 3. Rencana Implementasi Code (Revised)

### Langkah 1: Fix Toleransi SR (Quick Win)
Ubah default tolerance di `is_near_support_resistance` dari `0.02` menjadi `0.003` (0.3%).

### Langkah 2: Implementasi ADX Filter
Di `src/indicators/technical.py` dan `signal_generator.py`:
```python
adx = calculate_adx(highs, lows, closes, period=14)
if adx < 20:
    return "NEUTRAL", 0.0, {} # Filter out choppy markets
```

### Langkah 3: Update Logika Sinyal (Trigger)
Ubah syarat RSI oversold murni menjadi RSI + Price Action:
```python
# Pseudo-code untuk Trigger
is_bullish_candle = current_close > current_open and current_close > previous_high
if rsi < 30 and is_bullish_candle:
    return "BUY"
```
