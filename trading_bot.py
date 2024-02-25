import asyncio
from config import *
from strategy import *
from getinfo import *
from helper import *
import os
import math
import requests
import json
import time
from datetime import datetime
from binance.client import Client
from binance.exceptions import BinanceAPIException
from colorama import init, Fore, Style
import traceback


async def main():
    # Initialize colorama
    init()

    # Initialize Binance client
    client = Client(api_key, api_secret)

    # Define your trading bot logic here
    while True:        
        # Get info        
        current_price = get_current_price(symbol)
        entry_price = current_price
        position_side = get_position_side(symbol)
        position_size = calculate_position_size(account_balance, leverage, symbol, percentage, stop_loss, take_profit)
        btc_quantity_size = round(position_size, 3)
        position_direction = ''  # Assign a default value to position_direction
        
        # Strategy
        super_trend_direction = get_super_trend_direction(symbol)
        alligator = get_alligator_direction(symbol)
        pp_super_trend = get_pivot_point_supertrend_direction(symbol)
        ema_cross = get_ema_crossover_direction(symbol)
        high_low = get_high_low(symbol)

        if ema_cross == 'BUY': 
            position_direction = 'LONG'  
        elif ema_cross =='SELL': 
            position_direction = 'SHORT'  
        elif ema_cross =='NEUTRAL': 
            position_direction = 'NEUTRAL'
            pass  
        
        sl_price, tp_price = calculate_stop_loss_take_profit_prices(position_direction, entry_price, stop_loss, take_profit)
        sl_last_candle = get_stop_loss_price_hl(symbol, position_direction)
        
        print('==================')
        print(Fore.YELLOW + f'Current {symbol} Price: {current_price}' + Style.RESET_ALL)
        print(Fore.GREEN + f'Account Balance: {round(account_balance, 2)} USDT' + Style.RESET_ALL)
        print(Fore.YELLOW + "Technical Analysis" + Style.RESET_ALL)
        # print(f'Super Trend: {super_trend_direction}')
        # print(f'Alligator: {alligator}')
        print(f'Ema_Cross: {ema_cross}')
        print(f'Stoploss_Candle_HL: {sl_last_candle}')
        print(f'Stoploss_%: {sl_price},{tp_price}')
        # print(f'HighLow: {high_low}')
        # print(f'Pivot Trend: {pp_super_trend}' + Style.RESET_ALL)
        print('==================')

        # Loop through open orders and print stop loss and take profit prices by position direction
        open_orders = get_open_orders(symbol)
        for order in open_orders:
            if order['type'] == 'STOP_LOSS_LIMIT':
                if order['positionSide'] == 'SHORT':
                    sl_price = float(order['stopPrice'])
                    print(f'Short Position Stop Loss Price: {sl_price}')
                elif order['positionSide'] == 'LONG':
                    sl_price = float(order['stopPrice'])
                    print(f'Long Position Stop Loss Price: {sl_price}')
            elif order['type'] == 'TAKE_PROFIT_LIMIT':
                if order['positionSide'] == 'SHORT':
                    tp_price = float(order['stopPrice'])
                    print(f'Short Position Take Profit Price: {tp_price}')
                elif order['positionSide'] == 'LONG':
                    tp_price = float(order['stopPrice'])
                    print(f'Long Position Take Profit Price: {tp_price}')

        # Use try to catch any Errors
        try:
            # ////////////////////////////////////////////////////////////////////////////////////////////////////
            # Place order condition
            if check_position_exists(symbol) and check_open_orders(client, symbol):
                print(Fore.YELLOW + "Position already exists" + Style.RESET_ALL)
                #position details
                position_details = get_position_details(symbol)
                entry_detail = float(position_details['entryPrice'])
                quantity_detail = float(position_details['positionAmt'])
                unrealized_pnl = float(position_details['unRealizedProfit'])
                sl_detail = sl_price
                tp_detail = tp_price
                # Print position details
                print(Fore.CYAN + f"Position Details for {symbol}:")
                print(f"Entry Price: {entry_detail}")
                print(f"Quantity: {quantity_detail}")
                print(f"Unrealized PNL: {unrealized_pnl} USDT" + Style.RESET_ALL)
                print('==================')
                print(Fore.YELLOW + 'Missed a position?' + Style.RESET_ALL)
                print(f'Position Status: {position_direction}')
                print(f"Stop Loss: {sl_detail}")
                print(f"Take Profit: {tp_detail}")

                # Check if trailing stop loss is enabled in config
                if trailing_stop_loss_enabled:
                    trailing_stop_loss(symbol, trailing_stop_loss_percentage)


                # Close position when direction flip
                if position_side == 'LONG' and position_direction == 'SHORT':
                    print('flip long to short, close position trigger')
                    client.futures_create_order(symbol=symbol, closePosition=true(Close-All), recvWindow=6000)
                else:
                    pass 
                if position_side == 'SHORT' and position_direction == 'LONG':
                    print('flip short to long, close position trigger')
                    client.futures_create_order(symbol=symbol, closePosition=true(Close-All), recvWindow=6000)
                else:
                    pass 
                    

            # CREATE THE ORDERS ///////////////////////////////////////
            else:
                if position_direction == 'LONG':
                    print('execute LONG Position')
                    print(f'Quantity LONG:{btc_quantity_size}')
                    # client.futures_create_order(symbol=symbol, side=Client.SIDE_BUY, 
                    #                             type=Client.ORDER_TYPE_MARKET,
                    #                             quantity=btc_quantity_size, 
                    #                             closePosition=False,
                    #                             reduceOnly=False,
                    #                             priceProtect=False,
                    #                             activationPrice=current_price,
                    #                             leverage=leverage,
                    #                             recvWindow=6000)

                elif position_direction == 'SHORT':
                    print('execute SHORT Position')
                    print(f'Quantity SHORT:{btc_quantity_size}')
                    # client.futures_create_order(symbol=symbol, side=Client.SIDE_SELL, 
                    #                             type=Client.ORDER_TYPE_MARKET,
                    #                             quantity=btc_quantity_size, 
                    #                             closePosition=False,
                    #                             reduceOnly=False,
                    #                             priceProtect=False,
                    #                             activationPrice=current_price,
                    #                             leverage=leverage,
                    #                             recvWindow=6000) 

            # Cancel all orders if no position
            if position_side == None:
                orders = client.futures_get_open_orders(symbol=symbol)
                client.futures_cancel_order(symbol=symbol, orderId=order['orderId'])
            else:
                pass


        except Exception as e:
            # handle exception
            print(f"Error: {e}")
            # optionally, sleep for some time before trying again
            time.sleep(5)
            continue        
        
        # based on the market conditions and technical analysis signals
        # Wait for a few seconds before checking the market again
        await asyncio.sleep(5)

    


if __name__ == '__main__':
    asyncio.run(main())
    
