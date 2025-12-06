import unittest
import numpy as np
from src.indicators.technical import calculate_rsi, calculate_ema, calculate_macd
from src.indicators.ngtcv import calculate_ngtCV, calculate_average_volume

class TestIndicators(unittest.TestCase):
    
    def test_calculate_rsi(self):
        """Test RSI calculation with known values"""
        # Test with flat prices (should be 50)
        prices = [100, 100, 100, 100, 100]
        rsi = calculate_rsi(prices)
        self.assertEqual(rsi, 50.0)
        
        # Test with increasing prices (should be 100)
        prices = [100, 110, 120, 130, 140]
        rsi = calculate_rsi(prices, period=2)
        self.assertAlmostEqual(rsi, 100.0, places=1)
        
        # Test with decreasing prices (should be 0)
        prices = [100, 90, 80, 70, 60]
        rsi = calculate_rsi(prices, period=2)
        self.assertAlmostEqual(rsi, 0.0, places=1)
    
    def test_calculate_ema(self):
        """Test EMA calculation"""
        prices = [10, 12, 11, 13, 14, 13, 12, 14, 15, 16]
        ema = calculate_ema(prices, 5)
        # EMA calculation should return a float value
        self.assertIsInstance(ema, float)
        self.assertGreater(ema, 0)
        
        # Test with insufficient data
        prices_short = [10, 12]
        ema_short = calculate_ema(prices_short, 5)
        self.assertIsInstance(ema_short, float)
        
    def test_calculate_macd(self):
        """Test MACD calculation"""
        prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
                 110, 112, 111, 113, 115, 114, 116, 118, 117, 119,
                 120, 12, 121, 123, 125, 124, 126, 128, 127, 129]
        
        macd_line, signal_line, histogram = calculate_macd(prices)
        
        # All values should be floats
        self.assertIsInstance(macd_line, float)
        self.assertIsInstance(signal_line, float)
        self.assertIsInstance(histogram, float)
        
        # Test with insufficient data
        prices_short = [100, 102, 101]
        macd_short = calculate_macd(prices_short)
        self.assertEqual(macd_short, (0.0, 0.0, 0.0))
    
    def test_calculate_ngtCV(self):
        """Test ngtCV calculation"""
        candle = {
            'open': 100,
            'close': 105,
            'high': 107,
            'low': 99,
            'volume': 1000,
            'historical_volumes': [900, 950, 1000, 1100, 980, 1020, 990, 1010, 970, 1030]
        }
        
        ngtcv, body_size, wick_ratio, volume_factor = calculate_ngtCV(candle)
        
        # All values should be floats
        self.assertIsInstance(ngtcv, float)
        self.assertIsInstance(body_size, float)
        self.assertIsInstance(wick_ratio, float)
        self.assertIsInstance(volume_factor, float)
        
        # ngtcv should be between -1 and 1
        self.assertGreaterEqual(ngtcv, -1.0)
        self.assertLessEqual(ngtcv, 1.0)
    
    def test_calculate_average_volume(self):
        """Test average volume calculation"""
        volumes = [1000, 1200, 800, 1100, 900]
        avg_vol = calculate_average_volume(volumes)
        
        self.assertIsInstance(avg_vol, float)
        self.assertEqual(avg_vol, 1000.0)  # (1000+1200+800+1100+900)/5
        
        # Test with insufficient data
        avg_vol_short = calculate_average_volume([1000])
        self.assertIsInstance(avg_vol_short, float)
        
        # Test with empty list
        avg_vol_empty = calculate_average_volume([])
        self.assertIsInstance(avg_vol_empty, float)
        self.assertEqual(avg_vol_empty, 1000)  # Default fallback

if __name__ == '__main__':
    unittest.main()