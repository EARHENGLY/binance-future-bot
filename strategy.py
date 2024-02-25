from config import *
import numpy as np
import pandas as pd
from binance.client import Client
import os
import ta
import time
import talib

# Initialize Binance client
client = Client(api_key, api_secret)


# STRATEGIES ////////////////////
# Super Trend
def get_super_trend_direction(symbol):
    klines = client.futures_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=500)
    close_prices = np.array([float(entry[4]) for entry in klines])
    high_prices = np.array([float(entry[2]) for entry in klines])
    low_prices = np.array([float(entry[3]) for entry in klines])
    atr_period = 10
    multiplier = 3.0
    hl2 = (high_prices + low_prices) / 2
    hl2_atr = talib.SMA(hl2, atr_period)
    hl2_atr *= multiplier
    st_upper = hl2 + hl2_atr
    st_lower = hl2 - hl2_atr
    st_direction = 1
    st_signal = []
    for i in range(1, len(close_prices)):
        if close_prices[i] > st_upper[i-1]:
            st_direction = 1
            st_signal.append('Sell')
            st_upper[i] = max(st_upper[i], st_lower[i-1] + hl2_atr[i])
            st_lower[i] = st_lower[i-1] + hl2_atr[i]
        else:
            st_direction = -1
            st_signal.append('Buy')
            st_upper[i] = st_upper[i-1] - hl2_atr[i]
            st_lower[i] = min(st_lower[i], st_upper[i-1] - hl2_atr[i])
        if st_direction == 1 and close_prices[i] < st_lower[i]:
            st_direction = -1
            st_signal[-1] = 'Buy'
            st_upper[i] = hl2[i] + hl2_atr[i]
            st_lower[i] = hl2[i] - hl2_atr[i]
        elif st_direction == -1 and close_prices[i] > st_upper[i]:
            st_direction = 1
            st_signal[-1] = 'Sell'
            st_upper[i] = hl2[i] - hl2_atr[i]
            st_lower[i] = hl2[i] + hl2_atr[i]
    if st_signal[-1] == 'Buy':
        return 'BUY'
    elif st_signal[-1] == 'Sell':
        return 'SELL'
    else:
        return 'NEUTRAL'
    
# Alligator
def get_alligator_direction(symbol):
    klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=500)
    df = pd.DataFrame(klines, columns=['Open time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume', 'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'])
    df['Close'] = df['Close'].astype(float)
    df['Jaw'] = df['Close'].rolling(13).mean()
    df['Teeth'] = df['Close'].rolling(8).mean()
    df['Lips'] = df['Close'].rolling(5).mean()
    if df['Lips'].iloc[-1] > df['Teeth'].iloc[-1] > df['Jaw'].iloc[-1]:
        return 'BUY'
    elif df['Jaw'].iloc[-1] > df['Teeth'].iloc[-1] > df['Lips'].iloc[-1]:
        return 'SELL'
    else:
        return 'NEUTRAL'
    
# Pivot Point with Super Trend
def get_pivot_point_supertrend_direction(symbol):
    klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=500)
    high_prices = [float(kline[2]) for kline in klines]
    low_prices = [float(kline[3]) for kline in klines]
    close_prices = [float(kline[4]) for kline in klines]
    pivot = (high_prices[0] + low_prices[0] + close_prices[0]) / 3
    supertrend = [pivot]
    atr = [0]
    for i in range(1, len(close_prices)):
        high_low_diff = high_prices[i] - low_prices[i]
        high_close_diff = abs(high_prices[i] - close_prices[i - 1])
        low_close_diff = abs(low_prices[i] - close_prices[i - 1])
        true_range = max(high_low_diff, high_close_diff, low_close_diff)
        atr_val = ((atr[-1] * 13) + true_range) / 14
        atr.append(atr_val)
        if close_prices[i] > supertrend[i-1] and supertrend[i-1] <= low_prices[i-1]:
            supertrend_val = max(supertrend[i-1], pivot - atr_val)
        else:
            supertrend_val = min(supertrend[i-1], pivot + atr_val)
        supertrend.append(supertrend_val)
    last_supertrend = supertrend[-1]
    last_close_price = close_prices[-1]
    if last_close_price > last_supertrend:
        return 'BUY'
    elif last_close_price < last_supertrend:
        return 'SELL'
    else:
        return 'NEUTRAL'


def get_ema_crossover_direction(symbol):
    klines = client.futures_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=500)

    # Extract the relevant OHLCV data from the klines
    ohlcv_data = []
    for kline in klines:
        open_time = pd.to_datetime(kline[0], unit='ms')
        close_time = pd.to_datetime(kline[6], unit='ms')
        open_price = float(kline[1])
        high_price = float(kline[2])
        low_price = float(kline[3])
        close_price = float(kline[4])
        volume = float(kline[5])
        ohlcv_data.append([open_time, close_time, open_price, high_price, low_price, close_price, volume])

    # Create a pandas DataFrame from the OHLCV data
    df = pd.DataFrame(ohlcv_data, columns=['OpenTime', 'CloseTime', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df.set_index('CloseTime', inplace=True)

    # Calculate the 50-period and 200-period EMA
    ema_50 = ta.trend.ema_indicator(close=df['Close'], window=50)
    ema_200 = ta.trend.ema_indicator(close=df['Close'], window=200)

    # Determine the direction based on the crossover of EMA50 and EMA200
    latest_ema_50 = ema_50.iloc[-1]
    latest_ema_200 = ema_200.iloc[-1]
    previous_ema_50 = ema_50.iloc[-2]
    previous_ema_200 = ema_200.iloc[-2]

    if latest_ema_50 > latest_ema_200 and previous_ema_50 <= previous_ema_200:
        return 'BUY'
    elif latest_ema_50 < latest_ema_200 and previous_ema_50 >= previous_ema_200:
        return 'SELL'
    else:
        return 'NEUTRAL'


def get_stop_loss_price_hl(symbol, position_direction): #Get SL TP by last amount candle
    klines = client.futures_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=500)

    # Extract the relevant OHLCV data from the klines
    ohlcv_data = []
    for kline in klines:
        open_time = pd.to_datetime(kline[0], unit='ms')
        close_time = pd.to_datetime(kline[6], unit='ms')
        open_price = float(kline[1])
        high_price = float(kline[2])
        low_price = float(kline[3])
        close_price = float(kline[4])
        volume = float(kline[5])
        ohlcv_data.append([open_time, close_time, open_price, high_price, low_price, close_price, volume])

    # Create a pandas DataFrame from the OHLCV data
    df = pd.DataFrame(ohlcv_data, columns=['OpenTime', 'CloseTime', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df.set_index('CloseTime', inplace=True)

    if position_direction == 'LONG':
        stop_loss_price_hl = df['Low'].tail(50).min()   # tail amount candle
    elif position_direction == 'SHORT':
        stop_loss_price_hl = df['High'].tail(50).max()    # tail amount candle
    elif position_direction == 'NEUTRAL':
        stop_loss_price_hl = 0
    return stop_loss_price_hl


def get_high_low(symbol):  #Get Support Resistance
    klines = client.futures_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_5MINUTE, limit=500)

    # Extract the relevant OHLCV data from the klines
    ohlcv_data = []
    for kline in klines:
        open_time = pd.to_datetime(kline[0], unit='ms')
        close_time = pd.to_datetime(kline[6], unit='ms')
        open_price = float(kline[1])
        high_price = float(kline[2])
        low_price = float(kline[3])
        close_price = float(kline[4])
        volume = float(kline[5])
        ohlcv_data.append([open_time, close_time, open_price, high_price, low_price, close_price, volume])

    # Create a pandas DataFrame from the OHLCV data
    df = pd.DataFrame(ohlcv_data, columns=['OpenTime', 'CloseTime', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df.set_index('CloseTime', inplace=True)

    # Calculate the support and resistance levels
    low = df['Low'].min()
    high = df['High'].max()

    return high, low 
