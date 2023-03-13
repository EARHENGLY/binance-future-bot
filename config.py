# Binance API credentials
api_key = 'xRWtFDt7xfA644Jf3enyVC9zNsxNeNAOZZClax1o8J4quujYbxNHVLAHPyaHtdnO'
api_secret = 'dYRymjneVaUxLJtgahEpngr7MAFSs0kOvtMv5qBeaH5ZsKUCdlRuzMNgQryaTswr'


# Trading parameters
symbol = 'BTCUSDT'
percentage = 0.001  #percentage of the account balance to risk
leverage = 50
risk_reward_ratio = 3  #risk reward ratio default 3
stop_loss = 0.01  # 1% stop loss of the current market price
take_profit = stop_loss * risk_reward_ratio

# Trailing stop loss configuration
trailing_stop_loss_enabled = True
trailing_stop_loss_percentage = 1  # 0.5% trailing stop loss