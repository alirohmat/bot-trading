# Advanced Trading Bot

Bot trading otomatis dengan analisis multi-indikator (RSI, EMA, MACD, ngtCV) dan sistem notifikasi Telegram. Bot ini telah ditingkatkan untuk mengatasi berbagai masalah dan kelemahan yang teridentifikasi.

## Fitur Baru 🚀

- **Keamanan**: Credentials disimpan aman di file `.env`
- **Multi-Indikator**: Menggabungkan RSI, EMA, MACD, dan ngtCV
- **Risk Management**: Stop Loss, Take Profit, dan Confidence Threshold
- **Struktur Modular**: Kode terorganisir di folder `src/`
- **Performance Tracking**: Win rate dan statistik akurasi real-time
- **State Persistence**: Data tidak hilang saat bot restart
- **OOP Approach**: Refactored dengan pendekatan Object-Oriented Programming
- **Improved Error Handling**: Dengan logging traceback lengkap
- **Interruptible Sleep**: Bot dapat dihentikan dengan CTRL+C

## Struktur Project

```
bot_trading/
├── .env                # File konfigurasi rahasia (Token, Chat ID)
├── config.py           # Konfigurasi bot & strategi
├── trading_bot.py      # Main entry point (OOP-based)
├── requirements.txt    # Dependencies
├── revisi.md           # Daftar perbaikan dan analisis
└── src/
    ├── data/           # Binance API handler
    ├── indicators/     # Technical indicators (RSI, EMA, MACD, ngtCV)
    ├── strategy/       # Signal generation logic
    ├── notifications/  # Telegram handler
    └── utils/          # Logger & helpers
```

## Instalasi

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup Environment**
   - Copy file `.env.example` menjadi `.env`
   - Isi token Telegram Anda di file `.env`:
     ```
     TELEGRAM_BOT_TOKEN=your_token_here
     TELEGRAM_CHAT_ID=your_chat_id_here
     ```

3. **Konfigurasi (Opsional)**
   - Buka `config.py` untuk mengubah:
     - Pair trading (`SYMBOL`)
     - Timeframe (`INTERVAL`)
     - Parameter indikator
     - Risk management settings

## Penggunaan

Jalankan bot dengan perintah:

```bash
python trading_bot.py
```

## Perbaikan Berdasarkan Analisis

Bot telah ditingkatkan berdasarkan analisis dalam file `revisi.md` dengan perbaikan-perbaikan berikut:

### 1. Perbaikan Indikator ngtCV
- **Masalah**: Indikator `ngtCV` tidak menggunakan volume dalam perhitungan meskipun volume_factor sudah dihitung
- **Perbaikan**: Menambahkan volume_factor ke dalam rumus perhitungan ngtCV sesuai dengan bobot yang ditentukan di config.py
- **Konfigurasi**: Bobot volume diatur di `NGTCV_WEIGHTS['volume']` di config.py

### 2. Perbaikan Fungsi MACD
- **Masalah**: Fungsi `calculate_macd` hanya mengembalikan MACD line, bukan signal line dan histogram
- **Perbaikan**: Implementasi lengkap MACD dengan perhitungan EMA untuk signal line dan histogram
- **Output**: Fungsi kini mengembalikan `(macd_line, signal_line, histogram)`

### 3. Perbaikan Mekanisme Sleep
- **Masalah**: Penggunaan `time.sleep()` yang panjang membuat bot sulit dihentikan
- **Perbaikan**: Mengganti dengan loop dengan sleep pendek (1 detik) agar bisa diinterupsi dengan CTRL+C
- **Durasi**: Bot menunggu 900 detik (15 menit) atau 3600 detik (1 jam) tergantung interval

### 4. Penambahan Persistensi State
- **Masalah**: Data hilang saat bot restart
- **Perbaikan**: Menyimpan state ke file JSON (`data/state.json`) termasuk:
  - `previous_prediction`: Prediksi sebelumnya
  - `previous_candle`: Candle sebelumnya
  - `prediction_stats`: Statistik akurasi (correct, incorrect, total, win_rate)

### 5. Refactoring ke OOP
- **Masalah**: Pendekatan prosedural dengan variabel global
- **Perbaikan**: Membuat class `TradingBot` untuk mengelola state dan fungsi-fungsi utama
- **Keuntungan**: Lebih mudah di-maintain dan diuji

### 6. Perbaikan Logging
- **Masalah**: Error handling hanya menampilkan pesan tanpa traceback lengkap
- **Perbaikan**: Menambahkan `exc_info=True` untuk menampilkan traceback lengkap saat error
- **Lokasi**: Di fungsi utama dan fungsi fetch_ohlcv_data

### 7. Perbaikan Validasi Konfigurasi
- **Masalah**: Validasi hanya menampilkan warning tanpa menghentikan program
- **Perbaikan**: Mengganti dengan `raise ValueError` agar program berhenti jika token Telegram kosong

## Strategi Trading

Bot menggunakan sistem scoring -3 sampai +3:

1. **RSI (14)**:
   - Oversold (<30) -> +1 point
   - Overbought (>70) -> -1 point

2. **EMA Trend (12/26)**:
   - Golden Cross/Bullish -> +1 point
   - Death Cross/Bearish -> -1 point

3. **MACD (12/26/9)**:
   - MACD line > signal line -> +1 point
   - MACD line < signal line -> -1 point

4. **ngtCV (Custom)**:
   - Strong Bullish (>0.1) -> +1 point
   - Strong Bearish (<-0.1) -> -1 point

**Sinyal:**
- **BUY**: Score >= +2 (Confidence tinggi)
- **SELL**: Score <= -2 (Confidence tinggi)
- **HOLD**: Score di antara -1 dan +1

## Metodologi & Penjelasan Indikator

### 1. RSI (Relative Strength Index)

**Konsep:**
RSI mengukur momentum harga dengan membandingkan kekuatan pergerakan naik vs turun dalam periode tertentu (default: 14 candle).

**Formula:**
```
RSI = 100 - (100 / (1 + RS))
RS = Average Gain / Average Loss
```

**Interpretasi:**
- **RSI > 70**: Pasar overbought (jenuh beli) → kemungkinan koreksi turun → Sinyal SELL
- **RSI < 30**: Pasar oversold (jenuh jual) → kemungkinan rebound naik → Sinyal BUY
- **RSI 30-70**: Kondisi normal

### 2. EMA (Exponential Moving Average)

**Konsep:**
EMA adalah rata-rata bergerak yang memberikan bobot lebih pada harga terbaru, sehingga lebih responsif terhadap perubahan harga dibanding SMA.

**Formula:**
```
EMA_today = (Price_today × K) + (EMA_yesterday × (1 - K))
K = 2 / (Period + 1)
```

**Strategi Golden/Death Cross:**
- **Golden Cross**: EMA Short (12) > EMA Long (26) → Trend Bullish → Sinyal BUY
- **Death Cross**: EMA Short (12) < EMA Long (26) → Trend Bearish → Sinyal SELL

### 3. MACD (Moving Average Convergence Divergence)

**Konsep:**
MACD menggabungkan EMA untuk mengidentifikasi momentum dan arah tren.

**Komponen:**
- **MACD Line**: EMA(12) - EMA(26)
- **Signal Line**: EMA(9) dari MACD Line
- **Histogram**: MACD Line - Signal Line

**Strategi:**
- **Bullish Crossover**: MACD line > Signal line → Sinyal BUY
- **Bearish Crossover**: MACD line < Signal line → Sinyal SELL

### 4. ngtCV (Custom Candle Value Indicator)

**Konsep:**
Indikator custom yang menganalisis kualitas candle berdasarkan:
- **Body**: Ukuran tubuh candle (selisih open-close)
- **Wick**: Panjang bayangan (upper + lower shadow)
- **Volume**: Konfirmasi kekuatan tren (baru ditambahkan)

**Formula:**
```
Total_Range = High - Low
Body_Ratio = |Close - Open| / Total_Range
Wick_Ratio = (Upper_Shadow + Lower_Shadow) / Total_Range
Direction = 1 if Close > Open else -1
Volume_Factor = Volume / Average_Volume

ngtCV = (Body_Ratio × Direction × 0.6) - (Wick_Ratio × 0.2) + (Volume_Factor × 0.2)
```

**Interpretasi:**
- **ngtCV > 0.1**: Candle bullish kuat (body besar, wick kecil) → BUY
- **ngtCV < -0.1**: Candle bearish kuat → SELL
- Wick besar mengurangi kekuatan sinyal (indikasi indecision/rejection)
- Volume tinggi memperkuat sinyal tren

### 5. Kombinasi Multi-Indikator

Bot menggunakan **voting system** untuk menghindari false signals:

**Contoh Skenario 1 - Strong BUY Signal:**
```
RSI = 25 (oversold)          → +1 point
EMA: Short > Long (bullish)  → +1 point
MACD: Line > Signal (bull)   → +1 point
ngtCV = 0.15 (strong bull)   → +1 point
-------------------------------------------
Total Score = +4             → BUY ✅
Confidence = 4/4 = 100%
```

**Contoh Skenario 2 - Conflicting Signals:**
```
RSI = 75 (overbought)        → -1 point
EMA: Short > Long (bullish)  → +1 point
MACD: Line < Signal (bear)   → -1 point
ngtCV = 0.05 (neutral)       → 0 point
-------------------------------------------
Total Score = -1             → HOLD ⏸️
Confidence = 25%
```

**Contoh Skenario 3 - Moderate SELL:**
```
RSI = 45 (neutral)           → 0 point
EMA: Short < Long (bearish)  → -1 point
MACD: Line < Signal (bear)   → -1 point
ngtCV = -0.12 (strong bear) → -1 point
-------------------------------------------
Total Score = -3             → SELL ✅
Confidence = 3/4 = 75%
```

### 6. Risk Management

Bot memiliki built-in risk management (dapat diatur di `config.py`):

```python
RISK_MANAGEMENT = {
    'max_risk_per_trade': 0.02,   # 2% maximum risk
    'stop_loss_pct': 0.02,        # 2% stop loss
    'take_profit_pct': 0.04,      # 4% take profit (1:2 R/R)
    'min_confidence': 0.6         # Minimum 60% confidence
}
```

**Catatan:** Risk management saat ini masih konseptual. Untuk trading real, perlu implementasi order management yang sebenarnya.

### 7. Evaluasi Akurasi

Bot mencatat setiap prediksi dan membandingkannya dengan hasil aktual:

```python
Prediction = BUY (prediksi harga naik)
Next Candle Close > Previous Close → Correct ✅
Win Rate = (Correct Predictions / Total Predictions) × 100%
```

**Threshold Evaluasi:**
- Perubahan harga < 0.1% dianggap noise (tidak dievaluasi)
- Hanya prediksi BUY/SELL yang dievaluasi (HOLD diabaikan)

## Kontribusi

Jika Anda menemukan bug atau memiliki saran perbaikan, silakan buat issue atau pull request. Perubahan-perubahan yang telah dilakukan mengikuti rekomendasi dari file `revisi.md`.

## Disclaimer

Bot ini adalah alat bantu simulasi. **Gunakan dengan risiko Anda sendiri.** Penulis tidak bertanggung jawab atas kerugian finansial yang mungkin terjadi.