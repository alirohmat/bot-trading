import requests
from src.utils.logger import setup_logger

logger = setup_logger()

def send_telegram(message: str, bot_token: str, chat_id: str) -> bool:
    """
    Mengirim notifikasi ke Telegram
    """
    if not bot_token or not chat_id:
        logger.warning("Telegram bot token atau chat ID belum diisi")
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Telegram message sent")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending message to Telegram: {e}")
        return False

def format_signal_message(symbol: str, interval: str, signal: str, confidence: float, price: float, indicators: dict) -> str:
    """
    Format pesan sinyal trading
    """
    icon = "🟢" if signal == "BUY" else "🔴"
    
    msg = f"{icon} *TRADING SIGNAL: {signal}*\n\n"
    msg += f"Symbol: `{symbol}`\n"
    msg += f"Interval: `{interval}`\n"
    msg += f"Price: `{price}`\n"
    msg += f"Confidence: `{confidence:.2f}`\n\n"
    
    msg += "*Indicators:*\n"
    msg += f"RSI: `{indicators.get('rsi', 0):.2f}`\n"
    msg += f"EMA Trend: `{indicators.get('ema_trend', 'N/A')}`\n"
    msg += f"ngtCV: `{indicators.get('ngtcv', 0):.4f}`\n"
    
    return msg
