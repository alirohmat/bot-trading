import logging
from src.data.binance_api import fetch_ohlcv_data, fetch_ohlcv_data_multiple_timeframes
from src.strategy.signal_generator import analyze_market, generate_signal, evaluate_prediction, calculate_atr_based_targets
from config import SYMBOL, INTERVAL

# Setup simple logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()

def run_backtest():
    logger.info(f"Starting Backtest for {SYMBOL} {INTERVAL}...")
    
    # Fetch max possible data (1000 candles) for both timeframes
    limit = 1000
    data = fetch_ohlcv_data(SYMBOL, INTERVAL, limit)
    
    # Fetch higher timeframe data for True Multi-Timeframe (1H)
    higher_timeframe_data = fetch_ohlcv_data(SYMBOL, "1h", limit)
    
    if not data:
        logger.error("Failed to fetch data")
        return

    logger.info(f"Fetched {len(data)} candles for {INTERVAL}")
    logger.info(f"Fetched {len(higher_timeframe_data)} candles for 1h")
    
    stats = {
        'total_signals': 0,
        'correct': 0,
        'incorrect': 0,
        'total_pnl': 0.0
    }
    
    # Simulation Loop
    start_index = max(50, 200) # Ensure enough data for 200 EMA
    
    active_trade = None # {type: 'BUY/SELL', entry_price: float, sl: float, tp: float, time: str}
    trades_history = []
    
    # We iterate through data one by one
    for i in range(start_index, len(data)):
        current_candle = data[i]
        current_time = current_candle['close_time']
        current_price = current_candle['close']
        current_high = current_candle['high']
        current_low = current_candle['low']
        
        # 1. Manage Active Trade
        if active_trade:
            # Check if TP or SL hit during this candle
            # Conservative assumption: Low happens before High? We don't know intra-candle path.
            # We'll check if BOTH are hit, it's usually bad luck (hit SL first), but let's check one by one.
            
            pnl = 0
            exit_reason = None
            
            if active_trade['type'] == 'BUY':
                # Check SL (Logic: Low touches SL)
                if current_low <= active_trade['sl']:
                    exit_price = active_trade['sl']
                    pnl = (exit_price - active_trade['entry_price']) / active_trade['entry_price'] * 100
                    exit_reason = "SL"
                # Check TP (Logic: High touches TP)
                elif current_high >= active_trade['tp']:
                    exit_price = active_trade['tp']
                    pnl = (exit_price - active_trade['entry_price']) / active_trade['entry_price'] * 100
                    exit_reason = "TP"
                    
            elif active_trade['type'] == 'SELL':
                # Check SL (Logic: High touches SL)
                if current_high >= active_trade['sl']:
                    exit_price = active_trade['sl']
                    pnl = (active_trade['entry_price'] - exit_price) / active_trade['entry_price'] * 100
                    exit_reason = "SL"
                # Check TP (Logic: Low touches TP)
                elif current_low <= active_trade['tp']:
                    exit_price = active_trade['tp']
                    pnl = (active_trade['entry_price'] - exit_price) / active_trade['entry_price'] * 100
                    exit_reason = "TP"
            
            if exit_reason:
                active_trade['exit_time'] = current_time
                active_trade['pnl'] = pnl
                active_trade['result'] = "WIN" if pnl > 0 else "LOSS"
                
                if pnl > 0:
                    stats['correct'] += 1
                else:
                    stats['incorrect'] += 1
                
                stats['total_pnl'] += pnl
                trades_history.append(active_trade)
                active_trade = None # Trade closed
                
            # If trade is still active, continue (skip generating new signal to avoid pyramiding for now)
            continue

        # 2. Generate New Signal (Only if no trade is active)
        # Analysis window uses data UP TO specific index (don't peep into future)
        # Note: fetch_ohlcv_data returns list, so we slice data[:i+1]
        # BUT analyze_market function expects the last item to be the 'current' finalized candle?
        # Actually in live bot, fetch_ohlcv returns finalized candles? Usually yes.
        
        analysis_window = data[:i+1]
        # Ambil data timeframe yang lebih tinggi untuk periode yang sesuai
        higher_tf_window = higher_timeframe_data[:i+1] if higher_timeframe_data else None
        trend, confidence, indicators = analyze_market(analysis_window, higher_tf_window)
        signal, conf = generate_signal((trend, confidence, indicators))
        
        # Debug: Tampilkan informasi jika tidak ada sinyal tetapi kondisi menarik
        if signal == "HOLD":
            # Tampilkan setiap kali ada potensi sinyal tetapi tidak terjadi
            adx = indicators.get('adx', 0)
            rsi = indicators.get('rsi', 0)
            trend_filter = indicators.get('trend_filter', 'N/A')
            is_bullish_engulfing = indicators.get('is_bullish_engulfing', False)
            is_bearish_engulfing = indicators.get('is_bearish_engulfing', False)
            
            # Tampilkan jika ada kondisi yang hampir memicu sinyal
            if (rsi < 35 and trend_filter == "BULLISH") or (rsi > 65 and trend_filter == "BEARISH"):
                logger.debug(f"Near Signal - Index {i}: ADX={adx:.2f}, RSI={rsi:.2f}, Trend={trend_filter}, Conf={confidence:.2f}, BullishEng={is_bullish_engulfing}, BearishEng={is_bearish_engulfing}")
        
        if signal != "HOLD":
            # Open new trade
            stats['total_signals'] += 1
            entry_price = current_price
            atr = indicators.get('atr', 0)
            
            if atr == 0:
                logger.warning(f"ATR 0 at {current_time}, skipping trade")
                continue
                
            stop_loss, take_profit = calculate_atr_based_targets(entry_price, atr)
            
            # Correction: current logic in signal_generator.py calculates SL/TP based on direction
            # But the helper function calculate_atr_based_targets handles calculation generically (Entry +/- ATR)
            # We need to map it correctly to Buy/Sell
            
            sl_dist = abs(entry_price - stop_loss)
            tp_dist = abs(entry_price - take_profit)
            
            real_sl = 0
            real_tp = 0
            
            if signal == "BUY":
                real_sl = entry_price - (entry_price - stop_loss) # stop_loss returned is Entry - (SL_mult * ATR)
                real_tp = entry_price + (take_profit - entry_price) # take_profit returned is Entry + (TP_mult * ATR)
            elif signal == "SELL":
                 # Logic in helper might assumes 'Long' calculation. Let's manually calculate to be safe or reuse params
                 # Config: SL mult = 2, TP mult = 3
                 # SELL SL = Entry + 2*ATR
                 # SELL TP = Entry - 3*ATR
            
                # Check how calculate_atr_based_targets is implemented in source
                # It does: sl = price - (mult*atr), tp = price + (mult*atr) -> This is for LONG
                
                from config import RISK_MANAGEMENT
                sl_mult = RISK_MANAGEMENT['atr_multiplier_sl']
                tp_mult = RISK_MANAGEMENT['atr_multiplier_tp']
                
                real_sl = entry_price + (sl_mult * atr)
                real_tp = entry_price - (tp_mult * atr)
            
            # Tambahkan informasi tambahan dari perubahan yang telah dibuat
            # Termasuk informasi posisi terhadap support/resistance
            sr_position = indicators.get('sr_position', 'AWAY_FROM_LEVELS')
            
            active_trade = {
                'type': signal,
                'entry_price': entry_price,
                'sl': real_sl,
                'tp': real_tp,
                'entry_time': current_time,
                'sr_position': sr_position,  # Tambahkan informasi posisi terhadap support/resistance
                'trend_filter': indicators.get('trend_filter', 'N/A'),  # Tambahkan informasi filter tren
                'rsi': indicators.get('rsi', 0),  # Tambahkan nilai RSI
                'ema_trend': indicators.get('ema_trend', 'N/A'),  # Tambahkan informasi tren EMA
                'adx': indicators.get('adx', 0),  # Tambahkan nilai ADX
                'is_bullish_engulfing': indicators.get('is_bullish_engulfing', False),  # Tambahkan informasi price action
                'is_bearish_engulfing': indicators.get('is_bearish_engulfing', False) # Tambahkan informasi price action
            }


    # Report
    if stats['total_signals'] > 0:
        win_rate = (stats['correct'] / stats['total_signals']) * 100
        logger.info("-" * 40)
        logger.info(f"BACKTEST RESULTS ({stats['total_signals']} signals)")
        logger.info("-" * 40)
        for trade in trades_history:
            # Format time from timestamp if needed, but assuming string or readable
            # binance_api returns close_time as timestamp (ms) usually.
            # Let's format it.
            import datetime
            ts = trade.get('entry_time', 0) / 1000
            dt = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
            sr_pos = trade.get('sr_position', 'N/A')
            trend_filter = trade.get('trend_filter', 'N/A')
            rsi = trade.get('rsi', 0)
            adx = trade.get('adx', 0)
            is_bullish_engulfing = trade.get('is_bullish_engulfing', False)
            is_bearish_engulfing = trade.get('is_bearish_engulfing', False)
            logger.info(f"{dt} | {trade['type']} | PnL: {trade['pnl']:.2f}% | {trade['result']} | SR: {sr_pos} | TF: {trend_filter} | RSI: {rsi:.1f} | ADX: {adx:.1f} | Engulf: B:{is_bullish_engulfing}, S:{is_bearish_engulfing}")
            
        logger.info("-" * 40)
        logger.info(f"Win Rate: {win_rate:.2f}%")
        logger.info(f"Correct:  {stats['correct']}")
        logger.info(f"Incorrect: {stats['incorrect']}")
        logger.info(f"Est. Net PnL (No Fees): {stats['total_pnl']:.2f}%")
        logger.info("-" * 40)
    else:
        logger.info("No signals generated in this period.")
        logger.info(f"Total candles processed: {len(data)}")
        logger.info(f"Start index: {start_index}")
        # Debug: Check some values during the simulation
        if len(data) > start_index:
            sample_analysis = analyze_market(data[start_index:start_index+100], higher_timeframe_data[start_index:start_index+100] if higher_timeframe_data else None)
            logger.info(f"Sample analysis result: {sample_analysis}")
            # Tampilkan semua kunci dalam dictionary indikator
            if len(sample_analysis) > 2 and sample_analysis[2]:
                logger.info(f"Full indicators: {sample_analysis[2]}")
                logger.info(f"Comment: {sample_analysis[2].get('comment', 'No comment')}")
            else:
                logger.info("No indicators returned")
            
            # Coba analisis dengan data yang lebih awal
            sample_analysis_early = analyze_market(data[start_index:start_index+50], higher_timeframe_data[start_index:start_index+50] if higher_timeframe_data else None)
            logger.info(f"Sample analysis early: {sample_analysis_early}")

if __name__ == "__main__":
    run_backtest()
