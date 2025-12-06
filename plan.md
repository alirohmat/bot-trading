# Rencana Perbaikan Kode Berdasarkan Laporan Revisi

Berdasarkan analisis file `revisi.md` dan kode sumber yang terkait, berikut adalah rencana perbaikan yang akan dilakukan:

## 1. Memperbaiki Kesalahan Logika (Logic Errors) & Bug Kritis

### A. Referensi Volume Hardcoded (`src/indicators/ngtcv.py`)

**Masalah**: Pada baris 48, referensi volume rata-rata di-hardcode:
```python
avg_volume_reference = 1000  # Nilai referensi
```

**Dampak**: Indikator ini **tidak valid** untuk aset dengan volume berbeda. Contoh: Volume 1000 BTC mungkin sangat tinggi, tapi 1000 SHIB sangat rendah. Ini membuat sinyal `ngtCV` menjadi bias dan tidak bisa dipercaya.

**Solusi**: Fungsi harus menerima data historis untuk menghitung *Moving Average Volume* (misal: rata-rata 20 candle terakhir) sebagai pembanding dinamis.

Perubahan yang diperlukan:
1. Memodifikasi fungsi `calculate_ngtCV` untuk menerima parameter tambahan berupa data volume historis
2. Menghitung rata-rata volume dari data historis sebagai referensi dinamis
3. Memperbarui pemanggilan fungsi ini di tempat lain dalam kode

### B. Inefisiensi Kalkulasi MACD (`src/indicators/technical.py`)

**Masalah**: Fungsi `calculate_macd` melakukan loop manual dan menghitung ulang EMA dari awal array untuk *setiap kali dipanggil*.

**Dampak**: Sangat lambat dan memboroskan CPU, terutama jika `limit` candle besar atau saat backtesting. Kompleksitas algoritmanya bisa menjadi kuadratik (O(n^2)) secara efektif karena re-kalkulasi berulang dalam loop tersembunyi.

**Solusi**: Gunakan vektorisasi dengan **Pandas** atau **Numpy** yang jauh lebih cepat dan efisien.

Perubahan yang diperlukan:
1. Mengimpor pandas dan numpy
2. Mengganti implementasi manual dengan fungsi vektorisasi
3. Menghitung EMA menggunakan `ewm()` dari pandas

### C. Type Safety pada State Persistence (`trading_bot.py`)

**Masalah**: Fungsi `load_state` mengembalikan tuple dari JSON, tetapi JSON secara inheren menyimpan urutan sebagai list.

**Dampak**: Meskipun Python saat ini mentoleransi unpacking list sebagai tuple, jika ada kode yang secara spesifik mengecek tipe data `isinstance(x, tuple)`, kode akan error.

**Solusi**: Explicit casting saat load: `tuple(state.get('previous_prediction'))`.

Perubahan yang diperlukan:
1. Memperbaiki fungsi `load_state` untuk mengonversi list kembali ke tuple
2. Menambahkan casting eksplisit saat memuat state

## 2. Saran Pengembangan & Optimasi

### A. Migrasi ke Pandas untuk Indikator

Saat ini indikator dihitung dengan loop Python murni. Ini tidak *scalable*.
**Rekomendasi**: Ubah `src/indicators/technical.py` untuk menggunakan `pandas.DataFrame` dan `ewm()`.

### B. Single Responsibility Principle pada Sinyal

Logika scoring di `src/strategy/signal_generator.py` terlalu sederhana (linear scoring +1/-1).
**Rekomendasi**:
1. Pisahkan logika entry dan exit.
2. Tambahkan filter volatilitas (misal: jangan trade jika Bollinger Bands terlalu sempit/squeeze).
3. Gunakan sistem bobot (weighted scoring) daripada poin integer sederhana.

### C. Manajemen Dependensi

File `requirements.txt` belum menyertakan `pandas` yang sangat disarankan untuk analisis data time-series.
**Rekomendasi**: Tambahkan `pandas>=1.3.0`.

### D. Unit Testing

Tidak ada tes otomatis untuk memastikan logika indikator benar.
**Rekomendasi**: Buat file `tests/test_indicators.py` untuk memvalidasi output indikator dibandingkan dengan nilai yang diketahui (misal dari library TA-Lib).

## 3. Rencana Implementasi

1. **Menambahkan pandas ke requirements.txt**
2. **Memperbaiki fungsi calculate_ngtCV untuk menggunakan volume referensi dinamis**
3. **Mengoptimalkan fungsi calculate_macd menggunakan pandas/numpy**
4. **Memperbaiki type safety pada state persistence di trading_bot.py**
5. **Membuat unit test untuk indikator**

## 4. Detail Teknis Perubahan

### Perubahan pada src/indicators/ngtcv.py:
- Menambahkan fungsi `calculate_average_volume` untuk menghitung rata-rata volume dari data historis
- Memodifikasi fungsi `calculate_ngtCV` untuk menerima parameter tambahan `historical_volumes`
- Memperbarui perhitungan volume_factor untuk menggunakan rata-rata volume historis sebagai referensi

### Perubahan pada src/indicators/technical.py:
- Menggunakan pandas untuk menghitung EMA dan MACD secara lebih efisien
- Mengganti loop manual dengan operasi vektorisasi

### Perubahan pada trading_bot.py:
- Memperbaiki fungsi `load_state` untuk mengonversi list kembali ke tuple saat memuat state

### Perubahan pada requirements.txt:
- Menambahkan `pandas>=1.3.0`

### Pembuatan file tests/test_indicators.py:
- Menambahkan unit test untuk memvalidasi fungsi-fungsi indikator