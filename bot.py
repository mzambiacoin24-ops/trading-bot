import os
import time
import requests
from binance.client import Client

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")  # FIXED
API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

CHAT_ID = None

client = None
if API_KEY and SECRET_KEY:
    client = Client(API_KEY, SECRET_KEY)

SYMBOL = "SOLUSDT"
TRADE_AMOUNT = 10
TP_PERCENT = 0.015
CHECK_SPEED = 5

in_trade = False
buy_price = 0

# ================= TELEGRAM =================
def send(msg):
    global CHAT_ID
    if CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        try:
            requests.post(url, json={"chat_id": CHAT_ID, "text": msg}, timeout=10)
        except:
            pass

def get_chat_id():
    global CHAT_ID
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    try:
        data = requests.get(url, timeout=10).json()
        if data.get("result"):
            CHAT_ID = data["result"][-1]["message"]["chat"]["id"]
            print("CHAT_ID:", CHAT_ID)
    except:
        pass

# ================= PRICE =================
def get_price():
    try:
        data = client.get_symbol_ticker(symbol=SYMBOL)
        return float(data["price"])
    except:
        return None

# ================= BUY =================
def buy():
    global in_trade, buy_price

    price = get_price()
    if not price:
        return

    buy_price = price
    in_trade = True

    tp = buy_price * (1 + TP_PERCENT)

    send(f"🟢 BUY START\n\nPrice: {buy_price:.2f}\nTP: {tp:.2f}")

# ================= SELL =================
def sell():
    global in_trade, buy_price

    price = get_price()
    if not price:
        return

    profit = (price - buy_price) * (TRADE_AMOUNT / buy_price)

    send(f"💰 TP HIT\n\nSell: {price:.2f}\nProfit: {profit:.2f}")

    in_trade = False

# ================= MAIN =================
print("🚀 BOT STARTING...")

while True:
    try:
        get_chat_id()

        if CHAT_ID:
            send("🚀 BOT ACTIVE")

            price = get_price()
            if not price:
                time.sleep(5)
                continue

            if not in_trade:
                buy()
            else:
                tp_price = buy_price * (1 + TP_PERCENT)
                if price >= tp_price:
                    sell()

        time.sleep(CHECK_SPEED)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(5)
