from src.data.binance_api import fetch_ohlcv_data, fetch_ohlcv_data_multiple_timeframes
from src.strategy.signal_generator import analyze_market
from config import SYMBOL, INTERVAL

# Ambil data
limit = 1000
data = fetch_ohlcv_data(SYMBOL, INTERVAL, limit)
higher_timeframe_data = fetch_ohlcv_data(SYMBOL, "1h", limit)

print(f"Fetched {len(data)} candles for {INTERVAL}")
print(f"Fetched {len(higher_timeframe_data)} candles for 1h")

if len(data) > 200:
    # Coba analisis dengan data awal yang cukup
    sample_data = data[200:400] # Ambil 200 candle setelah index 20
    sample_higher_tf = higher_timeframe_data[200:400] if len(higher_timeframe_data) > 200 else None
    
    print(f"Sample data length: {len(sample_data)}")
    print(f"Sample higher tf length: {len(sample_higher_tf) if sample_higher_tf else 0}")
    
    result = analyze_market(sample_data, sample_higher_tf)
    print(f"Analysis result: {result}")
    
    if len(result) > 2:
        print(f"Indicators: {result[2]}")
        if 'comment' in result[2]:
            print(f"Comment: {result[2]['comment']}")
        if 'adx' in result[2]:
            print(f"ADX value: {result[2]['adx']}")
        if 'rsi' in result[2]:
            print(f"RSI value: {result[2]['rsi']}")
        if 'trend_filter' in result[2]:
            print(f"Trend filter: {result[2]['trend_filter']}")
else:
    print("Not enough data")