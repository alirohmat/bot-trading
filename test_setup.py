import sys
import os
from dotenv import load_dotenv

print("Testing imports...")
try:
    from config import SYMBOL, TELEGRAM_BOT_TOKEN
    print(f"Config loaded. Symbol: {SYMBOL}")
    print(f"Token loaded: {'Yes' if TELEGRAM_BOT_TOKEN else 'No'}")
    
    from src.utils.logger import setup_logger
    logger = setup_logger(name="test_logger")
    print("Logger setup success")
    
    from src.indicators.technical import calculate_rsi
    rsi = calculate_rsi([10, 12, 11, 13, 15, 14, 16, 18, 17, 19, 21, 23, 22, 24, 25])
    print(f"RSI Calculation: {rsi:.2f}")
    
    from src.indicators.ngtcv import calculate_ngtCV
    candle = {'open': 100, 'close': 105, 'high': 110, 'low': 95, 'volume': 1000}
    ngtcv, _, _, _ = calculate_ngtCV(candle)
    print(f"ngtCV Calculation: {ngtcv:.4f}")
    
    print("\nALL TESTS PASSED ✅")
    
except Exception as e:
    print(f"\nTEST FAILED ❌: {e}")
    import traceback
    traceback.print_exc()
