import os
import time
import requests

# ================= CONFIG =================
TOKEN = os.getenv("TOKEN")

COINS = ["SOL-USDT"]

TRADE_AMOUNT = 10
MAX_BUYS = 5

TP_PERCENT = 0.01      # 🔥 profit kubwa
SL_PERCENT = 0.012

GRID_STEP = 1.5
CHECK_SPEED = 3

COOLDOWN_AFTER_TP = 30   # 🔥 inazuia trade spam

# ================= STATE =================
positions = []
base_price = None
CHAT_ID = None
active_symbol = None
in_trade = False
trade_opened = False
last_trade_close_time = 0

price_data = {c: [] for c in COINS}
last_market_msg_id = None

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

def market_watch(msg):
    global last_market_msg_id
    try:
        if last_market_msg_id is None:
            res = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={"chat_id": CHAT_ID, "text": msg}
            ).json()
            last_market_msg_id = res["result"]["message_id"]
        else:
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/editMessageText",
                json={
                    "chat_id": CHAT_ID,
                    "message_id": last_market_msg_id,
                    "text": msg
                }
            )
    except:
        pass

# ================= PRICE =================
def get_price(symbol):
    try:
        res = requests.get(
            "https://api.kucoin.com/api/v1/market/orderbook/level1",
            params={"symbol": symbol}
        ).json()
        return float(res["data"]["price"])
    except:
        return None

# ================= TREND =================
def detect_trend(h):
    if len(h) < 5:
        return "SIDE"
    if h[-1] > h[-5]:
        return "UP"
    elif h[-1] < h[-5]:
        return "DOWN"
    return "SIDE"

# ================= START =================
print("🚀 V10 SOL FINAL STARTED")

while CHAT_ID is None:
    get_chat_id()
    time.sleep(2)

send("🚀 GRID V10 (SOL FINAL) ACTIVE")

# ================= MAIN =================
while True:

    price = get_price("SOL-USDT")
    if price:
        price_data["SOL-USDT"].append(price)
        if len(price_data["SOL-USDT"]) > 20:
            price_data["SOL-USDT"].pop(0)

    if not in_trade and active_symbol is None:
        active_symbol = "SOL-USDT"

    if not active_symbol:
        time.sleep(CHECK_SPEED)
        continue

    price = price_data["SOL-USDT"][-1]
    trend = detect_trend(price_data["SOL-USDT"])

    # ================= OPEN GRID =================
    if (
        not in_trade
        and trend == "UP"
        and not trade_opened
        and (time.time() - last_trade_close_time > COOLDOWN_AFTER_TP)
    ):

        trade_opened = True
        in_trade = True

        base_price = price
        positions = []

        for i in range(MAX_BUYS):
            buy_price = price - (i * GRID_STEP)
            positions.append(buy_price)

        total_capital = MAX_BUYS * TRADE_AMOUNT
        avg_entry = sum(positions) / len(positions)
        tp = avg_entry * (1 + TP_PERCENT)

        msg = f"""📍 SOL-USDT

💰 Total Capital: ${total_capital}
📊 Entries: {MAX_BUYS}
📊 Avg Entry: {round(avg_entry,2)}
🎯 TP: {round(tp,2)}

"""

        for p in positions:
            msg += f"🟢 BUY {round(p,2)}\n"

        send(msg)

    # ================= TAKE PROFIT =================
    if in_trade and positions:
        avg = sum(positions) / len(positions)
        tp_price = avg * (1 + TP_PERCENT)

        if price >= tp_price:
            capital = len(positions) * TRADE_AMOUNT
            profit = capital * ((price - avg) / avg)

            send(f"""📤 TP HIT

🪙 SOL-USDT
💰 Capital: ${capital}
📊 Avg: {round(avg,2)}
📊 Exit: {round(price,2)}

💵 Profit: ${round(profit,2)}""")

            positions = []
            in_trade = False
            active_symbol = None
            trade_opened = False
            last_trade_close_time = time.time()   # 🔥 cooldown start

    # ================= STOP LOSS =================
    if in_trade and positions:
        avg = sum(positions) / len(positions)
        sl = avg * (1 - SL_PERCENT)

        if price <= sl:
            capital = len(positions) * TRADE_AMOUNT
            loss = capital * ((price - avg) / avg)

            send(f"""🛑 STOP LOSS

🪙 SOL-USDT
💰 Capital: ${capital}
📉 Loss: ${round(loss,2)}""")

            positions = []
            in_trade = False
            active_symbol = None
            trade_opened = False
            last_trade_close_time = time.time()

    # ================= MARKET =================
    msg = f"📊 SOL Market: {round(price,2)}"
    market_watch(msg)

    time.sleep(CHECK_SPEED)
