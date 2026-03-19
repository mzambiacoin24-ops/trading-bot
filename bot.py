import os
import time
import requests

# ==============================
# CONFIG
# ==============================
MODE = os.getenv("MODE", "paper")  # paper / live
TOKEN = os.getenv("TOKEN")

SYMBOL = "BTC-USDT"
TRADE_AMOUNT = 10  # dollar

TP_PERCENT = 0.002  # 0.2%
SL_PERCENT = 0.003  # 0.3%

CHECK_SPEED = 3

# ==============================
# STATE
# ==============================
in_position = False
buy_price = 0

balance = 100  # paper balance

# ==============================
# GET REAL PRICE (KUCOIN)
# ==============================
def get_price():
    try:
        url = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={SYMBOL}"
        res = requests.get(url).json()
        return float(res['data']['price'])
    except:
        return None

# ==============================
# BUY
# ==============================
def buy(price):
    global in_position, buy_price, balance

    if MODE == "paper":
        buy_price = price
        in_position = True
        print(f"🟢 BUY @ {price}")

    else:
        print("LIVE BUY (utaongezwa baadae)")

# ==============================
# SELL
# ==============================
def sell(price):
    global in_position, balance

    profit = price - buy_price

    if MODE == "paper":
        balance += profit
        print("🔴 SELL EXECUTED")
        print(f"💰 Balance: {round(balance,2)}")

    else:
        print("LIVE SELL (utaongezwa baadae)")

    in_position = False

# ==============================
# MAIN LOOP
# ==============================
def run_bot():
    global in_position

    print("🚀 BOT STARTED")

    while True:
        price = get_price()

        if price is None:
            print("Error kupata price...")
            time.sleep(CHECK_SPEED)
            continue

        print(f"Price: {price}")

        if not in_position:
            buy(price)

        else:
            tp = buy_price * (1 + TP_PERCENT)
            sl = buy_price * (1 - SL_PERCENT)

            if price >= tp or price <= sl:
                sell(price)

        time.sleep(CHECK_SPEED)

# ==============================
run_bot()
