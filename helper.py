import time
from config import *
from binance.client import Client
from binance.exceptions import BinanceAPIException
from decimal import Decimal
from getinfo import *


# Calculate StopLoss
def calculate_stop_loss_take_profit_prices(position_direction, entry_price, stop_loss, take_profit):
    if position_direction == 'LONG':
        sl_price = round(entry_price - (entry_price * stop_loss), 2)
        tp_price = round(entry_price + (entry_price * take_profit), 2)
    elif position_direction == 'SHORT': 
        sl_price = round(entry_price + (entry_price * stop_loss), 2)
        tp_price = round(entry_price - (entry_price * take_profit), 2)
    elif position_direction == 'NEUTRAL': 
        sl_price = 0
        tp_price = 0
    return sl_price, tp_price



# Get current position TP price
def get_take_profit_price(symbol):
    """Returns the take profit price for the given symbol."""
    position = client.futures_position_information(symbol=symbol)
    if position:
        if float(position[0]['positionAmt']) > 0:
            entry_price = float(position[0]['entryPrice'])
            take_profit_percentage = float(position[0]['takeProfitPercent'])
            take_profit_price = round(entry_price + (entry_price * take_profit_percentage), 2)
            return take_profit_price
        elif float(position[0]['positionAmt']) < 0:
            entry_price = float(position[0]['entryPrice'])
            take_profit_percentage = float(position[0]['takeProfitPercent'])
            take_profit_price = round(entry_price - (entry_price * take_profit_percentage), 2)
            return take_profit_price
    return None

# Get current position SL price
def get_stop_loss_price(symbol):
    """Returns the stop loss price for the given symbol."""
    position = client.futures_position_information(symbol=symbol)
    if position:
        if float(position[0]['positionAmt']) > 0:
            entry_price = float(position[0]['entryPrice'])
            stop_loss_percentage = float(position[0]['stopLossPercent'])
            stop_loss_price = round(entry_price - (entry_price * stop_loss_percentage), 2)
            return stop_loss_price
        elif float(position[0]['positionAmt']) < 0:
            entry_price = float(position[0]['entryPrice'])
            stop_loss_percentage = float(position[0]['stopLossPercent'])
            stop_loss_price = round(entry_price + (entry_price * stop_loss_percentage), 2)
            return stop_loss_price
    return None


#Error placing limit buy order for BTCUSDT: APIError(code=-4014): Price not increased by tick size.
# Retrieve symbol info from the exchange
current_price = get_current_price(symbol)
exchange_info = client.futures_exchange_info()
symbol_info = next(filter(lambda x: x['symbol'] == symbol, exchange_info['symbols']))
tick_size = float(symbol_info['filters'][0]['tickSize'])
price_limit_trail_stop = Decimal(str(current_price)).quantize(Decimal(str(tick_size)))


# limit buy sell order for trailing stop
def limit_buy_order(symbol, quantity, price):
        try:
            order = client.futures_create_order(
                symbol=symbol,
                side=Client.SIDE_BUY,
                type=Client.ORDER_TYPE_LIMIT,
                timeInForce=Client.TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=price_limit_trail_stop,
            )
            return order
        except BinanceAPIException as e:
            print(f"Error placing limit buy order for {symbol}: {e}")
            return None

def limit_sell_order(symbol, quantity, price):
    try:
        order = client.futures_create_order(
            symbol=symbol,
            side=Client.SIDE_SELL,
            type=Client.ORDER_TYPE_LIMIT,
            timeInForce=Client.TIME_IN_FORCE_GTC,
            quantity=quantity,
            price=price_limit_trail_stop,
        )
        return order
    except BinanceAPIException as e:
        print(f"Error placing limit sell order for {symbol}: {e}")
        return None


# Calculate the trailing stop ////////////////////////
def trailing_stop_loss(symbol, trailing_stop_loss_percentage):
        entry_price = get_entry_price(symbol)
        current_price = get_current_price(symbol)
        stop_loss_price = round(entry_price - (entry_price * trailing_stop_loss_percentage), 2)
        trailing_stop_price = entry_price
        position_side = get_position_side(symbol)
        quantity = get_quantity_position(symbol)
        exchange_info = client.futures_exchange_info()

        if position_side == 'LONG' and current_price > entry_price or position_side == 'SHORT' and current_price < entry_price:
            while True:
                current_price = get_current_price(symbol)
                if position_side == 'LONG':
                    if current_price > trailing_stop_price:
                        trailing_stop_price = current_price
                    elif current_price < stop_loss_price:
                        limit_sell_order(symbol, quantity, stop_loss_price)
                        break
                elif position_side == 'SHORT':
                    if current_price < trailing_stop_price:
                        trailing_stop_price = current_price
                    elif current_price > stop_loss_price:
                        limit_buy_order(symbol, quantity, stop_loss_price)
                        break
                new_trailing_stop_price = round(trailing_stop_price - (trailing_stop_price * trailing_stop_loss_percentage), 2)
                if new_trailing_stop_price > trailing_stop_price:
                    trailing_stop_price = new_trailing_stop_price
                time.sleep(1)
        else:
            print("Not in profit, trailing stop loss not activated.")
