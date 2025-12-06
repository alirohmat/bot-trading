import time
import sys
import json
from datetime import datetime
from typing import Optional, Tuple

# Import modules
from config import SYMBOL, INTERVAL, LIMIT, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from src.utils.logger import setup_logger
from src.data.binance_api import fetch_ohlcv_data
from src.strategy.signal_generator import analyze_market, generate_signal, evaluate_prediction
from src.notifications.telegram import send_telegram, format_signal_message

# Setup logger
logger = setup_logger()

# State file path
STATE_FILE = 'data/state.json'

class TradingBot:
    """
    Advanced Trading Bot using OOP approach
    """
    def __init__(self):
        self.logger = setup_logger()
        self.sleep_seconds = 900  # 15m default
        if INTERVAL == "1h":
            self.sleep_seconds = 3600

        # Initialize prediction stats
        self.prediction_stats = {
            'correct': 0,
            'incorrect': 0,
            'total': 0,
            'win_rate': 0.0
        }

        # Initialize state
        self.previous_prediction = None
        self.previous_candle = None
        self.previous_indicators = {}

    def start(self):
        """
        Start the trading bot
        """
        self.logger.info("Starting Advanced Trading Bot...")
        self.logger.info(f"Symbol: {SYMBOL}, Interval: {INTERVAL}")

        # Check credentials
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            self.logger.error("Telegram credentials missing! Please check .env file.")
            sys.exit(1)

        # Send startup message
        send_telegram(f"🚀 Bot Started\nSymbol: {SYMBOL}\nInterval: {INTERVAL}", TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

        # Load state from file if available
        self.previous_prediction, self.previous_candle, self.prediction_stats = load_state()

        self.main_loop()

    def main_loop(self):
        """
        Main execution loop
        """
        while True:
            try:
                self.logger.info(f"Fetching data...")
                data = fetch_ohlcv_data(SYMBOL, INTERVAL, LIMIT)

                if not data:
                    self.logger.warning("No data received, retrying in 60s...")
                    time.sleep(60)
                    continue

                current_candle = data[-1]
                current_price = current_candle['close']

                # 1. Evaluate Previous Prediction
                if self.previous_prediction and self.previous_candle:
                    # Ambil ATR dari indikator sebelumnya jika tersedia
                    atr_value = self.previous_indicators.get('atr') if hasattr(self, 'previous_indicators') else None
                    is_correct, pct_change = evaluate_prediction(self.previous_candle, current_candle, self.previous_prediction, atr_value)

                    if is_correct is not None:
                        if is_correct:
                            self.prediction_stats['correct'] += 1
                            self.logger.info(f"✅ Prediction CORRECT (+{pct_change:.2f}%)")
                        else:
                            self.prediction_stats['incorrect'] += 1
                            self.logger.info(f"❌ Prediction INCORRECT (-{pct_change:.2f}%)")

                        self.prediction_stats['total'] += 1
                        self.prediction_stats['win_rate'] = (self.prediction_stats['correct'] / self.prediction_stats['total']) * 100

                        # Send accuracy update
                        acc_msg = f"📊 Accuracy Update:\nWin Rate: {self.prediction_stats['win_rate']:.1f}%\n({self.prediction_stats['correct']}/{self.prediction_stats['total']})"
                        send_telegram(acc_msg, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

                        # Save state after updating stats
                        save_state(self.previous_prediction, self.previous_candle, self.prediction_stats)

                # 2. Analyze Market
                trend, confidence, indicators = analyze_market(data)
                self.logger.info(f"Analysis: {trend} (Conf: {confidence:.2f}) | RSI: {indicators.get('rsi', 0):.1f}")
                
                # 3. Generate Signal
                signal, conf = generate_signal((trend, confidence, indicators))
                
                if signal != "HOLD":
                    self.logger.info(f"🔔 SIGNAL: {signal}")
                    # Tambahkan informasi posisi terhadap support/resistance ke dalam pesan
                    sr_position = indicators.get('sr_position', 'AWAY_FROM_LEVELS')
                    msg = format_signal_message(SYMBOL, INTERVAL, signal, conf, current_price, indicators, sr_position)
                    send_telegram(msg, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
                
                # 4. Store State
                self.previous_prediction = (signal, conf)
                self.previous_candle = current_candle
                self.previous_indicators = indicators
                
                # Save state to file
                save_state(self.previous_prediction, self.previous_candle, self.prediction_stats)

                # Wait for next candle with interruptible sleep
                self.logger.info(f"Waiting {self.sleep_seconds}s...")
                # Use a loop with short sleep intervals to allow interruption
                slept = 0
                sleep_interval = 1  # 1 second intervals
                while slept < self.sleep_seconds:
                    time.sleep(sleep_interval)
                    slept += sleep_interval
                    # Check for keyboard interrupt in each iteration
                    if slept % 10 == 0:  # Every 10 seconds, log remaining time
                        self.logger.debug(f"Sleeping... {self.sleep_seconds - slept}s remaining")

            except KeyboardInterrupt:
                self.logger.info("Bot stopped by user")
                send_telegram("🛑 Bot Stopped", TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
                break
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}", exc_info=True)
                time.sleep(60)

def save_state(previous_prediction, previous_candle, prediction_stats):
    """Save bot state to JSON file"""
    try:
        state = {
            'previous_prediction': previous_prediction,
            'previous_candle': previous_candle,
            'prediction_stats': prediction_stats
        }
        # Create directory if it doesn't exist
        import os
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving state: {e}")

def load_state():
    """Load bot state from JSON file"""
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            # Convert list back to tuple for type safety
            previous_prediction = tuple(state.get('previous_prediction')) if state.get('previous_prediction') else None
            return previous_prediction, state.get('previous_candle'), state.get('prediction_stats', {
                'correct': 0,
                'incorrect': 0,
                'total': 0,
                'win_rate': 0.0
            })
    except FileNotFoundError:
        logger.info("State file not found, starting with fresh state")
        return None, None, {
            'correct': 0,
            'incorrect': 0,
            'total': 0,
            'win_rate': 0.0
        }
    except Exception as e:
        logger.error(f"Error loading state: {e}, starting with fresh state")
        return None, None, {
            'correct': 0,
            'incorrect': 0,
            'total': 0,
            'win_rate': 0.0
        }

def main_loop():
    """
    Wrapper function to maintain compatibility with existing code structure
    """
    bot = TradingBot()
    bot.start()

if __name__ == "__main__":
    main_loop()