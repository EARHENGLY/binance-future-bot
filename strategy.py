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


# Get the current price for the symbol.
def get_current_price(symbol):
    client = Client()  # create a new Binance API client instance
    ticker = client.get_symbol_ticker(symbol=symbol)  # get the ticker for the given symbol
    if 'price' not in ticker:
        raise ValueError(f"Failed to retrieve current price for symbol {symbol}")
    return float(ticker['price'])







# STRATEGIES ///////////////  BELOW  /////////////////////
#All Strategy Return As Neutral Buy and Sell


#Determines Inner Circle Trader bias for a symbol based on the EMA indicators.
def get_ict_bias(symbol: str) -> str:
    """
    Args:
        symbol (str): The symbol to get the bias for.
    Returns:
        str: The bias of the symbol (either 'Bullish', 'Bearish', or 'Neutral').
    """
    # Retrieve the historical klines for the symbol.
    klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=500)
    # Extract the closing prices from the klines.
    closes = np.array([float(kline[4]) for kline in klines])
    # Calculate the 12, 50, and 200 period EMAs.
    ema_12 = talib.EMA(closes, timeperiod=12)
    ema_50 = talib.EMA(closes, timeperiod=50)
    ema_200 = talib.EMA(closes, timeperiod=200)
    # Get the current price for the symbol.
    current_price = get_current_price(symbol)
    # Determine the bias based on the EMA indicators and current price.
    if current_price > ema_12[-1] and ema_12[-1] > ema_50[-1] and ema_50[-1] > ema_200[-1]:
        return 'Bullish'
    elif current_price < ema_12[-1] and ema_12[-1] < ema_50[-1] and ema_50[-1] < ema_200[-1]:
        return 'Bearish'
    else:
        return 'Neutral'
    


#Determines Smart Money Consepts
def get_smart_money_signal(symbol: str, limit: int = 500) -> str:
    """Function to get the Smart Money signal for a symbol"""
    klines = client.futures_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=limit)
    df = pd.DataFrame(klines, columns=['Open time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume',
                                    'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'])
    df = df[['Open time', 'Open', 'High', 'Low', 'Close', 'Volume']]
    df[['Open', 'High', 'Low', 'Close', 'Volume']] = df[['Open', 'High', 'Low', 'Close', 'Volume']].apply(pd.to_numeric)
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    direction = df['Close'] - df['Open']
    force = typical_price * df['Volume'] * direction
    force_ema = pd.Series.ewm(force, span=13).mean()
    volume_ema = pd.Series.ewm(df['Volume'], span=13).mean()
    smi = force_ema / volume_ema
    sma20 = pd.Series.rolling(df['Close'], window=20).mean()
    sma200 = pd.Series.rolling(df['Close'], window=200).mean()
    last_smi, last_sma20, last_sma200 = smi.iloc[-1], sma20.iloc[-1], sma200.iloc[-1]
    if last_smi > 0 and last_sma20 > last_sma200:
        return 'Buy'
    elif last_smi < 0 and last_sma20 < last_sma200:
        return 'Sell'
    else:
        return 'Neutral'
    



#Determines Super Trend
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
        return 'Bullish'
    elif st_signal[-1] == 'Sell':
        return 'Bearish'
    else:
        return 'Neutral'
    


#Determines Alligator
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
    



#Determines Pivot Point with Super Trend
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