import telegram
import platform
import os
import logging
import subprocess
import psutil
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, Updater, CallbackQueryHandler


bot_token = '6260552346:AAG36hexN8zyRFRU_DIDX3FTX0pHts1-dM0'
chat_id = '398173228'

bot = telegram.Bot(token=bot_token)

def get_trading_bot_status():
    system = platform.system()
    if system == 'Windows':
        print('Running on window')
        for proc in psutil.process_iter(['pid', 'name']):
            if 'trading_bot.py' in proc.info['name']:
                print('Trading bot is running')
                status = "Trading bot is running"
                break
        else:
            print('Trading bot is not running')
            status = "Trading bot is not running"
    elif system == 'Linux':
        print('Running on Linux')
        try:
            os.kill(os.popen("pgrep -f 'python3 trading_bot.py'").read().strip(), 0)
            print('Trading bot is running')
            status = "Trading bot is running"
        except:
            print('Trading bot is not running')
            status = "Trading bot is not running"
    else:
        status = "Unsupported operating system"
    return status
def start_trading_bot(update, context):
    system = platform.system()
    if system == 'Windows':
        for proc in psutil.process_iter(['pid', 'name']):
            if 'trading_bot.py' in proc.info['name']:
                context.bot.send_message(chat_id=update.message.chat_id, text="Trading bot is already running")
                break
        else:
            # start the trading bot
            python_path = r'C:\Users\CODEX\AppData\Local\Programs\Python\Python38\python.exe'  # replace with your Python executable path
            os.system(f'{python_path} trading_bot.py')
            context.bot.send_message(chat_id=update.message.chat_id, text="Trading bot started")

    elif system == 'Linux':
        try:
            os.kill(int(os.popen("pgrep -f 'python3 trading_bot.py'").read().strip()), 0)
            context.bot.send_message(chat_id=update.message.chat_id, text="Trading bot is already running")
        except:
            os.chdir('/path/to/trading_bot/')
            os.system("python3 trading_bot.py &")
            context.bot.send_message(chat_id=update.message.chat_id, text="Trading bot started")
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text="Unsupported operating system")


def stop_trading_bot(update, context):
    system = platform.system()
    if system == 'Windows':
        for proc in psutil.process_iter(['pid', 'name']):
            if 'python.exe' in proc.info['name']:
                cmdline = proc.cmdline()
                if len(cmdline) >= 2 and 'trading_bot.py' in cmdline[1]:
                    proc.kill()
                    if update.message:
                        context.bot.send_message(chat_id=update.message.chat_id, text="Trading bot stopped")
                    break
        else:
            if update.message:
                context.bot.send_message(chat_id=update.message.chat_id, text="Trading bot is not running")

    elif system == 'Linux':
        try:
            os.system("pkill -f 'python3 trading_bot.py'")
            if update.message:
                context.bot.send_message(chat_id=update.message.chat_id, text="Trading bot stopped")
        except:
            if update.message:
                context.bot.send_message(chat_id=update.message.chat_id, text="Trading bot is not running")
    else:
        if update.message:
            context.bot.send_message(chat_id=update.message.chat_id, text="Unsupported operating system")




def restart_trading_bot(update, context):
    stop_trading_bot(update, context)
    start_trading_bot(update, context)

def write_to_log(msg):
    with open('trading_bot.log', 'a') as f:
        f.write(msg + '\n')

def send_terminal_log(update, context):
    try:
        log_lines = subprocess.check_output(['tail', '-n', '50', 'trading_bot.log']).decode('utf-8')
        context.bot.send_message(chat_id=update.message.chat_id, text=f"Last 50 lines of trading_bot.log:\n{log_lines}")
    except subprocess.CalledProcessError:
        context.bot.send_message(chat_id=update.message.chat_id, text="Error: trading_bot.log not found")


def start(update, context):
    keyboard = [
        [InlineKeyboardButton("Trading Status", callback_data='tradingstatus')],
        [InlineKeyboardButton("Start Trading Bot", callback_data='startbot')],
        [InlineKeyboardButton("Stop Trading Bot", callback_data='stopbot')],
        [InlineKeyboardButton("Restart Trading Bot", callback_data='restartbot')],
        [InlineKeyboardButton("View Terminal Log", callback_data='send_terminal_log')],
        [InlineKeyboardButton("Option 2", callback_data='option2')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose an option:', reply_markup=reply_markup)


def button(update, context):
    query = update.callback_query
    if query.data == 'tradingstatus':
        status = get_trading_bot_status()
        context.bot.send_message(chat_id=query.message.chat_id, text=status)
    elif query.data == 'startbot':
        context.bot.send_message(chat_id=query.message.chat_id, text="Starting trading bot")
        start_trading_bot(update, context)
    elif query.data == 'stopbot':
        context.bot.send_message(chat_id=query.message.chat_id, text="Stopping trading bot")
        stop_trading_bot(update, context)
    elif query.data == 'restartbot':
        context.bot.send_message(chat_id=query.message.chat_id, text="Restarting trading bot")
        restart_trading_bot(update, context)
    elif query.data == 'viewlog':
        context.bot.send_message(chat_id=query.message.chat_id, text="This is the terminal logs")
        send_terminal_log(update, context)

    elif query.data == 'option2':
        context.bot.send_message(chat_id=query.message.chat_id, text="You selected Option 2")




updater = Updater(token=bot_token, use_context=True)
dispatcher = updater.dispatcher

# Create a command handler for the /tradingstatus command
trading_status_handler = CommandHandler('tradingstatus', get_trading_bot_status)
dispatcher.add_handler(trading_status_handler)

# Create handlers for the start command and button click
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)
updater.dispatcher.add_handler(CallbackQueryHandler(button, run_async=True))



updater.start_polling()