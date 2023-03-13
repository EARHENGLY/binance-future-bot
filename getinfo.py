import time
from config import *
from binance.client import Client
from binance.exceptions import BinanceAPIException
from decimal import Decimal

# Initialize Binance client
client = Client(api_key, api_secret)




# Get account Balance 
def get_account_balance(api_key, api_secret):
    client = Client(api_key, api_secret)
    balance = client.futures_account_balance()
    for asset in balance:
        if asset['asset'] == 'USDT':
            return float(asset['balance'])
    return 0.0
account_balance = get_account_balance(api_key, api_secret)


#Get position
def get_position(symbol):
    """Function to get the current position for a given symbol"""
    position = client.futures_position_information(symbol=symbol)
    for p in position:
        if p['symbol'] == symbol:
            return p
    return None


# Get the current price for the symbol.
def get_current_price(symbol):
    client = Client()  # create a new Binance API client instance
    ticker = client.get_symbol_ticker(symbol=symbol)  # get the ticker for the given symbol
    if 'price' not in ticker:
        raise ValueError(f"Failed to retrieve current price for symbol {symbol}")
    return float(ticker['price'])


# Calculate position size
def calculate_position_size(account_balance, leverage, symbol, percentage, stop_loss, take_profit):
    current_price = get_current_price(symbol)
    position_size = (account_balance * leverage * percentage) / ((current_price * stop_loss) - (current_price * take_profit))
    return position_size


# check_position_exists
def check_position_exists(symbol):
    """Function to check if a position already exists for a given symbol"""
    position = get_position(symbol)
    if position is not None:
        if float(position['positionAmt']) != 0:
            return True
    return False


# check_position_exists by ""Check open order""
def check_open_orders(client, symbol):
    """Function to check if there are any open orders for a given symbol"""
    orders = client.futures_get_open_orders(symbol=symbol)
    if orders:
        for order in orders:
            if order['status'] in ['NEW', 'PARTIALLY_FILLED']:
                return True
    return False


# Get position details
def get_position_details(symbol):
    """Function to get position details for a given symbol"""
    position_details = client.futures_position_information(symbol=symbol)[0]
    return position_details


# Get open orders for symbol
def get_open_orders(symbol):
    """Function to get open orders for a given symbol"""
    orders = client.futures_get_open_orders(symbol=symbol)
    return orders


# Current Position INFO ////////////////////////

# Get current position Entry Price
def get_entry_price(symbol):
    """Function to get the entry price of the last filled order for a given symbol"""
    position = client.futures_position_information(symbol=symbol)
    if position:
        entry_price = float(position[0]['entryPrice'])
        return entry_price
    return None

# Check current position is Long or Short 
def get_position_side(symbol):
    """Function to get the position side (LONG or SHORT) for a given symbol"""
    position = get_position(symbol)
    if position is not None:
        if float(position['positionAmt']) > 0:
            return 'LONG'
        elif float(position['positionAmt']) < 0:
            return 'SHORT'
    return None

# Get current position trading amount
def get_quantity_position(symbol):
    """Get the quantity of the currently open position"""
    position = get_position(symbol)
    if position is not None and float(position['positionAmt']) != 0:
        return abs(float(position['positionAmt']))
    return 0


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





# Calculate the trailing stop ////////////////////////

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


# Trailing Stop Function
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