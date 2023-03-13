import asyncio
from config import *
from strategy import *
from getinfo import *
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



    # Quantity to Trade, TakeProfit and StopLoss ///////////////////////////////////
    current_price = get_current_price(symbol)
    # Get current price and calculate order parameters  STOPLOSS TAKE PROFIT
    entry_price = current_price

    def calculate_stop_loss_take_profit_prices(position_direction, entry_price, stop_loss, take_profit):
        if position_direction == 'LONG':
            sl_price = round(entry_price - (entry_price * stop_loss), 2)
            tp_price = round(entry_price + (entry_price * take_profit), 2)
        else: 
            sl_price = round(entry_price + (entry_price * stop_loss), 2)
            tp_price = round(entry_price - (entry_price * take_profit), 2)
        return sl_price, tp_price


    position_size = calculate_position_size(account_balance, leverage, symbol, stop_loss, take_profit)
    btc_quantity_size = round(position_size, 3)





    # Define your trading bot logic here
    while True:
        #call function to run get SL TP for position
        sl_price, tp_price = calculate_stop_loss_take_profit_prices(position_direction, entry_price, current_price, stop_loss, take_profit)
        
        # get the current position for the symbol
        position = get_position_side(symbol)



        # Buy and sell orders, or any other trading operations
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



        print()
        print('////////////////////////////////////////////')
        print(Fore.YELLOW + f'Current {symbol} Price: {current_price}' + Style.RESET_ALL)
        print(Fore.GREEN + f'Account Balance: {round(get_account_balance(api_key, api_secret), 2)} USDT' + Style.RESET_ALL)
        print('==================')

        # Technical analysis direction
        print(Fore.YELLOW + "Technical Analysis" + Style.RESET_ALL)
        # Determine the Inner Circle Trader bias for the symbol
        ict_bias = get_ict_bias(symbol)
        print(Fore.BLUE + f'ICT Bias: {ict_bias}')
        # Determine the Smart Money signal for the symbol
        smart_money_signal = get_smart_money_signal(symbol)
        print(f'Smart Money: {smart_money_signal}')
        # Determine the SuperTrend direction for the symbol
        super_trend_direction = get_super_trend_direction(symbol)
        print(f'Super Trend: {super_trend_direction}')
        # Determine the Alligator direction for the symbol
        alligator = get_alligator_direction(symbol)
        print(f'Alligator: {alligator}')
        # Determine the Alligator direction for the symbol
        pp_super_trend = get_pivot_point_supertrend_direction(symbol)
        print(f'Pivot Trend: {pp_super_trend}' + Style.RESET_ALL)
        print('==================')
        print()

        # Determine the position direction based on the signals
        if ict_bias == 'Bullish' and smart_money_signal == 'Buy' and super_trend_direction == 'Bullish' and alligator == 'BUY' and pp_super_trend == 'BUY':
            position_direction = 'LONG'   #ict_bias == 'Bullish' and 
        elif ict_bias == 'Bearish' and smart_money_signal == 'Sell' and super_trend_direction == 'Bearish' and alligator == 'SELL' and pp_super_trend =='SELL':
            position_direction = 'SHORT'   #ict_bias == 'Bearish' and 
        else:
            position_direction = 'NONE'


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
                print('////////////////////////////////////////////')

                # Check if trailing stop loss is enabled in config
                if trailing_stop_loss_enabled:
                    # Call trailing_stop_loss function
                    trailing_stop_loss(symbol, trailing_stop_loss_percentage)

                # Check if the current opened position has sl and tp , if not create thr order 
                if sl_order is None and tp_order is None:
                # create stop-loss and take-profit orders if they don't already exist
                    client.order_stop_loss_take_profit(
                        symbol=symbol,
                        side=position['side'],
                        stop_loss={'stopPrice': sl_price},
                        take_profit={'stopPrice': tp_price},
                        type='STOP_LOSS_TAKE_PROFIT'
                    )
                    print(f"Stop-loss and take-profit orders set for {symbol}.")
                else:
                    print(f"Stop-loss and take-profit orders already exist for {symbol}.")


                pass


            # ////////////////////////////////////////////////////////////////////////////////////////////////////
            # CREATE THE ORDERS 
            else:
                if position_direction == 'LONG':
                    order = client.futures_create_order(symbol=symbol, side=Client.SIDE_BUY, type=Client.ORDER_TYPE_MARKET,
                                                        quantity=btc_quantity_size, 
                                                        newOrderRespType=Client.ORDER_RESP_TYPE_RESULT,
                                                        closePosition=False,
                                                        reduceOnly=False,
                                                        priceProtect=False,
                                                        activationPrice=current_price,
                                                        leverage=leverage,
                                                        recvWindow=6000)
                    
                    # Open take profit and stop loss orders
                    if order['orderId']:
                        # found position no sl tp 
                        order_placed = False
                        if current_price >= tp_price:
                            tp_order = client.futures_create_order(symbol=symbol, 
                                                                    side=Client.SIDE_SELL, 
                                                                    type=Client.ORDER_TYPE_TAKE_PROFIT_LIMIT,
                                                                    stopPrice=tp_price,
                                                                    price=tp_price,
                                                                    closePosition=True,
                                                                    newOrderRespType=Client.ORDER_RESP_TYPE_RESULT,
                                                                    recvWindow=6000)
                            if order['orderId']:
                                break
                        if current_price <= sl_price:
                            sl_order = client.futures_create_order(symbol=symbol, 
                                                                    side=Client.SIDE_SELL, 
                                                                    type=Client.ORDER_TYPE_STOP_LOSS_LIMIT,
                                                                    stopPrice=sl_price, 
                                                                    price=sl_price,
                                                                    closePosition=True,
                                                                    newOrderRespType=Client.ORDER_RESP_TYPE_RESULT,
                                                                    recvWindow=6000)
                            if order['orderId']:
                                break

                    # Cancel all orders if take profit or stop loss hit
                    if order_placed:
                        # Position has been closed
                        while True:
                            orders = client.futures_get_open_orders(symbol=symbol)
                            if not orders:
                                break
                            for order in orders:
                                client.futures_cancel_order(symbol=symbol, orderId=order['orderId'])
                    pass


                elif position_direction == 'SHORT':
                    order = client.futures_create_order(symbol=symbol, side=Client.SIDE_SELL, type=Client.ORDER_TYPE_MARKET,
                                                        quantity=btc_quantity_size, 
                                                        newOrderRespType=Client.ORDER_RESP_TYPE_RESULT,
                                                        closePosition=False,
                                                        reduceOnly=False,
                                                        priceProtect=False,
                                                        activationPrice=current_price,
                                                        leverage=leverage,
                                                        recvWindow=6000) 

                    # Open take profit and stop loss orders
                    if order['orderId']:
                        # found position no sl tp
                        order_placed = False
                        if current_price <= tp_price:
                            tp_order = client.futures_create_order(symbol=symbol, 
                                                                    side=Client.SIDE_BUY, 
                                                                    type=Client.ORDER_TYPE_TAKE_PROFIT_LIMIT,
                                                                    stopPrice=tp_price,
                                                                    price=tp_price,
                                                                    closePosition=True,
                                                                    newOrderRespType=Client.ORDER_RESP_TYPE_RESULT,
                                                                    recvWindow=6000)
                            if order['orderId']:
                                break
                        if current_price >= sl_price:
                            sl_order = client.futures_create_order(symbol=symbol, 
                                                                    side=Client.SIDE_BUY, 
                                                                    type=Client.ORDER_TYPE_STOP_LOSS_LIMIT,
                                                                    stopPrice=sl_price, 
                                                                    price=sl_price,
                                                                    closePosition=True,
                                                                    newOrderRespType=Client.ORDER_RESP_TYPE_RESULT,
                                                                    recvWindow=6000)
                            if order['orderId']:
                                break

                        # Cancel all orders if take profit or stop loss hit
                        if order_placed:
                            # Position has been closed
                            while True:
                                orders = client.futures_get_open_orders(symbol=symbol)
                                if not orders:
                                    break
                                for order in orders:
                                    client.futures_cancel_order(symbol=symbol, orderId=order['orderId'])

            # Print a message indicating that the position has been opened
            print(Fore.MAGENTA + f'Position Status: {position_direction} {round(position_size, 5)} {symbol} at {current_price}' + Style.RESET_ALL)

        except Exception as e:
            # handle exception
            print(f"Error: {e}")
            # optionally, sleep for some time before trying again
            time.sleep(5)
            continue        
        # ////////////////////////////////////////////////////////////////////////////////////////////////////


        
        # based on the market conditions and technical analysis signals
        # Wait for a few seconds before checking the market again
        await asyncio.sleep(15)



if __name__ == '__main__':
    asyncio.run(main())
