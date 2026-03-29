import os
import time
import requests
from binance.client import Client

# ================= CONFIG =================
TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

CHAT_ID = None

client = Client(API_KEY, SECRET_KEY)

SYMBOL = "SOLUSDT"
TRADE_AMOUNT = 10
TP_PERCENT = 0.015
CHECK_SPEED = 5

in_trade = False
buy_price = 0

# ================= TELEGRAM =================
def send(msg):
    if CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg})

def get_chat_id():
    global CHAT_ID
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    data = requests.get(url).json()
    if data["result"]:
        CHAT_ID = data["result"][-1]["message"]["chat"]["id"]

# ================= PRICE =================
def get_price():
    data = client.get_symbol_ticker(symbol=SYMBOL)
    return float(data["price"])

# ================= BUY =================
def buy():
    global in_trade, buy_price

    try:
        price = get_price()

        qty = round(TRADE_AMOUNT / price, 3)

        # NO REAL ORDER
        buy_price = price
        in_trade = True

        tp = buy_price * (1 + TP_PERCENT)

        send(f"🟢 BUY START\n\nPrice: {buy_price:.2f}\nTP: {tp:.2f}")

    except Exception as e:
        send(f"❌ BUY ERROR: {e}")

# ================= SELL =================
def sell():
    global in_trade, buy_price

    try:
        price = get_price()

        qty = round(TRADE_AMOUNT / buy_price, 3)
        profit = (price - buy_price) * qty

        # NO REAL ORDER
        send(f"💰 TP HIT\n\nSell: {price:.2f}\nProfit: {profit:.2f}")

        in_trade = False

    except Exception as e:
        send(f"❌ SELL ERROR: {e}")

# ================= MAIN =================
get_chat_id()
send("🚀 BOT ACTIVE")

while True:
    try:
        price = get_price()

        if not in_trade:
            buy()

        else:
            tp_price = buy_price * (1 + TP_PERCENT)

            if price >= tp_price:
                sell()

        time.sleep(CHECK_SPEED)

    except Exception as e:
        send(f"⚠️ ERROR: {e}")
        time.sleep(5)
