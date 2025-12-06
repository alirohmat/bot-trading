# Laporan Analisis & Revisi Codebase

Berdasarkan tinjauan menyeluruh terhadap source code, berikut adalah daftar kesalahan logika, masalah performa, dan saran pengembangan yang ditemukan:

## 1. 🐛 Kesalahan Logika (Logic Errors) & Bug Kritis

### A. Referensi Volume Hardcoded (`src/indicators/ngtcv.py`)
*   **Masalah**: Pada baris 48, referensi volume rata-rata di-hardcode:
    ```python
    avg_volume_reference = 1000  # Nilai referensi
    ```
*   **Dampak**: Indikator ini **tidak valid** untuk aset dengan volume berbeda. Contoh: Volume 1000 BTC mungkin sangat tinggi, tapi 1000 SHIB sangat rendah. Ini membuat sinyal `ngtCV` menjadi bias dan tidak bisa dipercaya.
*   **Solusi**: Fungsi harus menerima data historis untuk menghitung *Moving Average Volume* (misal: rata-rata 20 candle terakhir) sebagai pembanding dinamis.

### B. Inefisiensi Kalkulasi MACD (`src/indicators/technical.py`)
*   **Masalah**: Fungsi `calculate_macd` melakukan loop manual dan menghitung ulang EMA dari awal array untuk *setiap kali dipanggil*.
*   **Dampak**: Sangat lambat dan memboroskan CPU, terutama jika `limit` candle besar atau saat backtesting. Kompleksitas algoritmanya bisa menjadi kuadratik (O(n^2)) secara efektif karena re-kalkulasi berulang dalam loop tersembunyi.
*   **Solusi**: Gunakan vektorisasi dengan **Pandas** atau **Numpy** yang jauh lebih cepat dan efisien.

### C. Type Safety pada State Persistence (`trading_bot.py`)
*   **Masalah**: Fungsi `load_state` mengembalikan tuple dari JSON, tetapi JSON secara inheren menyimpan urutan sebagai list.
    ```python
    # Saat save: ("BUY", 0.9) -> JSON: ["BUY", 0.9]
    # Saat load: variabel menjadi list, bukan tuple.
    ```
*   **Dampak**: Meskipun Python saat ini mentoleransi unpacking list sebagai tuple, jika ada kode yang secara spesifik mengecek tipe data `isinstance(x, tuple)`, kode akan error.
*   **Solusi**: Explicit casting saat load: `tuple(state.get('previous_prediction'))`.

## 2. 🚀 Saran Pengembangan & Optimasi

### A. Migrasi ke Pandas untuk Indikator
Saat ini indikator dihitung dengan loop Python murni. Ini tidak *scalable*.
**Rekomendasi**: Ubah `src/indicators/technical.py` untuk menggunakan `pandas.DataFrame` dan `ewm()`.
```python
# Contoh Optimasi EMA
def calculate_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()
```

### B. Single Responsibility Principle pada Sinyal
Logika scoring di `src/strategy/signal_generator.py` terlalu sederhana (linear scoring +1/-1).
**Rekomendasi**:
1.  Pisahkan logika entry dan exit.
2.  Tambahkan filter volatilitas (misal: jangan trade jika Bollinger Bands terlalu sempit/squeeze).
3.  Gunakan sistem bobot (weighted scoring) daripada poin integer sederhana.

### C. Manajemen Dependensi
File `requirements.txt` belum menyertakan `pandas` yang sangat disarankan untuk analisis data time-series.
**Rekomendasi**: Tambahkan `pandas>=1.3.0`.

### D. Unit Testing
Tidak ada tes otomatis untuk memastikan logika indikator benar.
**Rekomendasi**: Buat file `tests/test_indicators.py` untuk memvalidasi output indikator dibandingkan dengan nilai yang diketahui (misal dari library TA-Lib).

---

## 3. Rencana Perbaikan (Action Plan)

Jika disetujui, saya dapat melakukan langkah-langkah berikut:

1.  **Refactor Indicators**: Menulis ulang `src/indicators/technical.py` menggunakan Numpy/Pandas.
2.  **Fix ngtCV**: Memperbaiki logika volume agar dinamis berdasarkan rata-rata historis.
3.  **Update Strategy**: Menyesuaikan `analyze_market` agar memanfaatkan indikator yang sudah dioptimasi.

Apakah Anda ingin saya mulai dengan perbaikan nomor 1 (Refactor Indicators) atau memperbaiki bug volume (Fix ngtCV) terlebih dahulu?
