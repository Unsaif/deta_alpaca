import requests
import os
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import TimeFrame, TimeFrameUnit
from dotenv import load_dotenv
import math
from urllib.error import HTTPError
import time

from deta import app

load_dotenv()

key_id = os.getenv("APCA_API_KEY_ID")
secret_key = os.getenv("APCA_API_SECRET_KEY")
base_url = 'https://paper-api.alpaca.markets'
trade_url = 'https://ebm573.deta.dev/stocks_to_buy'

def calculate_quantity(price):
    quantity = math.floor(5000/price)
    return quantity

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

        for ticker in stocks_to_buy:
            if ticker in symbols:
                print(f"{ticker} in symbols")
                continue
            else:
                try:
                    ticker_bars = api.get_bars(ticker, TimeFrame(1, TimeFrameUnit.Minute)).df.iloc[0]
                    ticker_price = ticker_bars['close']

                    qty = calculate_quantity(ticker_price)

                    api.submit_order(symbol=ticker, 
                    qty=qty, 
                    side='buy', 
                    type='market', 
                    time_in_force='day',
                    take_profit=dict(
                        limit_price=ticker_price*1.2
                    ))

                    waiting = True
                    while waiting:
                        try:
                            api.submit_order(symbol=ticker,
                            qty=qty,
                            side="sell",
                            type="trailing_stop",
                            time_in_force="gtc",
                            trail_percent=20)
                            
                            waiting = False
                        except Exception as err:
                            print(err)
                            print("waiting")
                            time.sleep(0.5)
                            continue
                except Exception as err:
                    print(f"{ticker} could not be purchased")
                    print(err)
                    continue
    else:
        print("No stonks today")