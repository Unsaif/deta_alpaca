from urllib.error import HTTPError
import requests
import os
import alpaca_trade_api as tradeapi
from dotenv import load_dotenv
import math
import time

from deta import app

load_dotenv()

key_id = os.getenv("APCA_API_KEY_ID")
secret_key = os.getenv("APCA_API_SECRET_KEY")
base_url = 'https://paper-api.alpaca.markets'
trade_url = 'https://ebm573.deta.dev/stocks_to_buy'

def calculate_quantity(price):
    quantity = math.floor(10000/price)
    return quantity

#
@app.lib.cron()
def buy_stocks(event):
    """
    Buy congress stonks
    """
    response = requests.get(trade_url)
    stocks_to_buy = list(response.json())

    api = tradeapi.REST(key_id, secret_key, base_url)

    symbols = []
    for position in api.list_positions():
        symbols.append(position.symbol)

    # account = api.get_account()

    # buying_power = account.buying_power

    if len(stocks_to_buy) != 0:
        # notional = (float(buying_power)/2)/len(stocks_to_buy)
        print("No stonks today")

        for ticker in stocks_to_buy:
            if ticker in symbols:
                continue
            else:
                try:
                    latest_quote = api.get_latest_quote(ticker).ap

                    qty = calculate_quantity(latest_quote)

                    api.submit_order(symbol=ticker, 
                    qty=qty, 
                    side='buy', 
                    type='market', 
                    time_in_force='day',
                    take_profit=dict(
                        limit_price=latest_quote*1.2
                    ))

                    waiting = True
                    while waiting:
                        try:
                            api.submit_order(symbol=ticker,
                            qty=qty,
                            side="sell",
                            type="trailing_stop",
                            time_in_force="day",
                            trail_percent=20)
                            
                            waiting = False
                        except HTTPError:
                            time.sleep(5)
                except Exception as err:
                    print(f"{ticker} could not be purchased")
                    print(err)
                    pass