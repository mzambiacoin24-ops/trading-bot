import os
import time
import requests
from binance.client import Client

# ================= CONFIG =================
TOKEN = os.getenv("TOKEN")

API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

print("API:", API_KEY)
print("SECRET:", SECRET_KEY)
client = Client(API_KEY, SECRET_KEY)

client.API_URL = "https://testnet.binance.vision/api"

COINS = ["SOLUSDT"]

TRADE_AMOUNT = 10
MAX_BUYS = 5

TP_PERCENT = 0.015
SL_PERCENT = 0.007

GRID_STEP = 1.5
CHECK_SPEED = 3

# ================= STATE =================
positions = []
CHAT_ID = None
in_trade = False

# ================= TELEGRAM =================
def get_chat_id():
    global CHAT_ID
    try:
        data = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates").json()
        if data["result"]:
            CHAT_ID = data["result"][-1]["message"]["chat"]["id"]
    except:
        pass

def send(msg):
    if CHAT_ID:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg}
        )

# ================= PRICE (BINANCE) =================
def get_price():
    try:
        data = client.get_symbol_ticker(symbol="SOLUSDT")
        return float(data["price"])
    except:
        return None

# ================= START =================
print("🚀 BOT STARTED")

while CHAT_ID is None:
    get_chat_id()
    time.sleep(2)

send("🚀 BOT ACTIVE (BINANCE)")

# ================= MAIN =================
while True:

    price = get_price()

    if not price:
        time.sleep(CHECK_SPEED)
        continue

    # ================= BUY =================
    if not in_trade:
        positions = []

        for i in range(MAX_BUYS):
            buy_price = price - (i * GRID_STEP)

            try:
                client.order_market_buy(
                    symbol="SOLUSDT",
                    quantity=0.1
                )
            except Exception as e:
                send(f"❌ Buy Error: {e}")

            positions.append(buy_price)

        avg = sum(positions) / len(positions)
        tp = avg * (1 + TP_PERCENT)

        send(f"""🟢 BUY START

Avg: {round(avg,2)}
TP: {round(tp,2)}
""")

        in_trade = True

    # ================= TP =================
    if in_trade and positions:
        avg = sum(positions) / len(positions)
        tp_price = avg * (1 + TP_PERCENT)

        if price >= tp_price:
            try:
                client.order_market_sell(
                    symbol="SOLUSDT",
                    quantity=0.1 * len(positions)
                )
            except Exception as e:
                send(f"❌ Sell Error: {e}")

            profit = (price - avg) * len(positions)

            send(f"""💰 TP HIT

Profit: {round(profit,2)}
""")

            positions = []
            in_trade = False

    # ================= SL =================
    if in_trade and positions:
        avg = sum(positions) / len(positions)
        sl = avg * (1 - SL_PERCENT)

        if price <= sl:
            try:
                client.order_market_sell(
                    symbol="SOLUSDT",
                    quantity=0.1 * len(positions)
                )
            except Exception as e:
                send(f"❌ SL Error: {e}")

            send("🛑 STOP LOSS")

            positions = []
            in_trade = False

    time.sleep(CHECK_SPEED)
