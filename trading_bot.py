import time
import sys
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

# Global stats
prediction_stats = {
    'correct': 0,
    'incorrect': 0,
    'total': 0,
    'win_rate': 0.0
}

def main_loop():
    """
    Main execution loop
    """
    logger.info("Starting Advanced Trading Bot...")
    logger.info(f"Symbol: {SYMBOL}, Interval: {INTERVAL}")
    
    # Check credentials
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Telegram credentials missing! Please check .env file.")
        sys.exit(1)
        
    # Send startup message
    send_telegram(f"🚀 Bot Started\nSymbol: {SYMBOL}\nInterval: {INTERVAL}", TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    
    # Determine sleep time
    sleep_seconds = 900  # 15m default
    if INTERVAL == "1h":
        sleep_seconds = 3600
        
    previous_prediction = None
    previous_candle = None
    
    while True:
        try:
            logger.info(f"Fetching data...")
            data = fetch_ohlcv_data(SYMBOL, INTERVAL, LIMIT)
            
            if not data:
                logger.warning("No data received, retrying in 60s...")
                time.sleep(60)
                continue
                
            current_candle = data[-1]
            current_price = current_candle['close']
            
            # 1. Evaluate Previous Prediction
            if previous_prediction and previous_candle:
                is_correct, pct_change = evaluate_prediction(previous_candle, current_candle, previous_prediction)
                
                if is_correct is not None:
                    if is_correct:
                        prediction_stats['correct'] += 1
                        logger.info(f"✅ Prediction CORRECT (+{pct_change:.2f}%)")
                    else:
                        prediction_stats['incorrect'] += 1
                        logger.info(f"❌ Prediction INCORRECT (-{pct_change:.2f}%)")
                        
                    prediction_stats['total'] += 1
                    prediction_stats['win_rate'] = (prediction_stats['correct'] / prediction_stats['total']) * 100
                    
                    # Send accuracy update
                    acc_msg = f"📊 Accuracy Update:\nWin Rate: {prediction_stats['win_rate']:.1f}%\n({prediction_stats['correct']}/{prediction_stats['total']})"
                    send_telegram(acc_msg, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
            
            # 2. Analyze Market
            trend, confidence, indicators = analyze_market(data)
            logger.info(f"Analysis: {trend} (Conf: {confidence:.2f}) | RSI: {indicators.get('rsi', 0):.1f}")
            
            # 3. Generate Signal
            signal, conf = generate_signal((trend, confidence, indicators))
            
            if signal != "HOLD":
                logger.info(f"🔔 SIGNAL: {signal}")
                msg = format_signal_message(SYMBOL, INTERVAL, signal, conf, current_price, indicators)
                send_telegram(msg, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
            
            # 4. Store State
            previous_prediction = (signal, conf)
            previous_candle = current_candle
            
            # Wait for next candle
            logger.info(f"Waiting {sleep_seconds}s...")
            time.sleep(sleep_seconds)
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            send_telegram("🛑 Bot Stopped", TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main_loop()