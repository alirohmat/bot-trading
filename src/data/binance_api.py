import requests
import time
from typing import List, Dict, Optional
from src.utils.logger import setup_logger

logger = setup_logger()

def fetch_ohlcv_data(symbol: str, interval: str, limit: int) -> List[Dict]:
    """
    Mengambil data OHLCV dari API Binance dengan error handling dan retry
    """
    url = "https://api.binance.com/api/v3/klines"
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Mengonversi data ke format yang lebih mudah digunakan
            ohlcv_data = []
            for item in data:
                candle = {
                    'open_time': item[0],
                    'open': float(item[1]),
                    'high': float(item[2]),
                    'low': float(item[3]),
                    'close': float(item[4]),
                    'volume': float(item[5]),
                    'close_time': item[6],
                    'quote_asset_volume': float(item[7]),
                    'number_of_trades': item[8],
                    'taker_buy_base_asset_volume': float(item[9]),
                    'taker_buy_quote_asset_volume': float(item[10])
                }
                ohlcv_data.append(candle)
            
            return ohlcv_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from Binance API (Attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                return []
    return []
