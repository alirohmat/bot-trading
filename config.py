import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Konfigurasi dasar
SYMBOL = "BTCUSDT"  # Pasangan trading yang digunakan
INTERVAL = "15m"    # Interval waktu: "15m" untuk 15 menit, "1h" untuk 1 jam
LIMIT = 100         # Jumlah candle yang diambil dari API

# Konfigurasi Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("WARNING: Telegram credentials not found in .env file!")

# Parameter tambahan untuk analisis
THRESHOLD_MULTIPLIER = 0.05  # Multiplier untuk menentukan ambang tren (5%)

# Bobot ngtCV yang diperbarui
NGTCV_WEIGHTS = {
    'body': 0.6,      # Bobot dominan untuk body
    'wick': -0.2,     # Wick besar mengurangi kekuatan sinyal
    'volume': 0.2     # Volume sebagai konfirmasi
}

# Konfigurasi Indikator Teknikal
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

EMA_SHORT_PERIOD = 12
EMA_LONG_PERIOD = 26

# Risk Management
RISK_MANAGEMENT = {
    'max_risk_per_trade': 0.02,  # 2% dari portfolio
    'stop_loss_pct': 0.02,       # 2% stop loss
    'take_profit_pct': 0.04,     # 4% take profit (1:2 Risk/Reward)
    'min_confidence': 0.6        # Minimum confidence to trade
}