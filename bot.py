import os
import time
import requests

# ================= CONFIG =================
TOKEN = os.getenv("TOKEN")

SYMBOL = "BTC-USDT"
TRADE_AMOUNT = 10
MAX_BUYS = 5

BASE_TP = 0.002
SL_PERCENT = 0.003

GRID_SPACING = 20
CHECK_SPEED = 3

# ================= STATE =================
positions = []
base_price = None
CHAT_ID = None

last_buy_time = 0
BUY_COOLDOWN = 8

started = False

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

# ================= PRICE =================
def get_price():
    try:
        res = requests.get(
            "https://api.kucoin.com/api/v1/market/orderbook/level1",
            params={"symbol": SYMBOL}
        ).json()
        return float(res["data"]["price"])
    except:
        return None

# ================= TREND =================
price_history = []

def detect_trend():
    if len(price_history) < 5:
        return "SIDE"
    if price_history[-1] > price_history[-5]:
        return "UP"
    elif price_history[-1] < price_history[-5]:
        return "DOWN"
    return "SIDE"

# ================= START =================
print("🚀 V7 FULL STARTED")

while CHAT_ID is None:
    get_chat_id()
    time.sleep(2)

# ================= MAIN =================
while True:
    price = get_price()
    if not price:
        time.sleep(CHECK_SPEED)
        continue

    price_history.append(price)
    if len(price_history) > 20:
        price_history.pop(0)

    trend = detect_trend()

    if not started:
        send("🚀 GRID V7 ACTIVE")
        started = True

    if base_price is None:
        base_price = price

    current_time = time.time()

    # ================= BUY =================
    if len(positions) < MAX_BUYS and current_time - last_buy_time > BUY_COOLDOWN:

        if not positions:
            if price <= base_price:
                positions.append(price)
                last_buy_time = current_time

                total_capital = MAX_BUYS * TRADE_AMOUNT

                # dynamic TP
                if trend == "UP":
                    tp = price * 1.004
                elif trend == "DOWN":
                    tp = price * 1.0015
                else:
                    tp = price * (1 + BASE_TP)

                send(f"""📍 BASE: {round(base_price,2)}

💰 Total Capital (Grid): ${total_capital}
🎯 TP Target: {round(tp,2)}

🟢 BUY {round(price,2)}""")

        else:
            last_buy = positions[-1]

            if price <= last_buy - GRID_SPACING:
                positions.append(price)
                last_buy_time = current_time
                send(f"🟢 BUY {round(price,2)}")

    # ================= SELL =================
    if positions:
        avg_entry = sum(positions) / len(positions)

        if trend == "UP":
            tp_price = avg_entry * 1.004
        elif trend == "DOWN":
            tp_price = avg_entry * 1.0015
        else:
            tp_price = avg_entry * (1 + BASE_TP)

        if price >= tp_price:
            capital = len(positions) * TRADE_AMOUNT
            profit_percent = ((price - avg_entry) / avg_entry) * 100
            profit_usd = capital * (profit_percent / 100)

            send(f"""📤 TRADE CLOSED

🪙 {SYMBOL}
💰 Capital Used: ${capital}
📊 Entries: {len(positions)}
📊 Avg Entry: {round(avg_entry,2)}
📊 Exit Price: {round(price,2)}

💵 Profit: +${round(profit_usd,2)}
📈 ROI: +{round(profit_percent,2)}%""")

            positions = []
            base_price = price
            send(f"🔄 New Base: {round(base_price,2)}")

    # ================= STOP LOSS =================
    if positions:
        avg_entry = sum(positions) / len(positions)
        sl_price = avg_entry * (1 - SL_PERCENT)

        if price <= sl_price:
            capital = len(positions) * TRADE_AMOUNT
            loss_percent = ((price - avg_entry) / avg_entry) * 100
            loss_usd = capital * (loss_percent / 100)

            send(f"""🛑 STOP LOSS HIT

🪙 {SYMBOL}
💰 Capital Used: ${capital}
📊 Avg Entry: {round(avg_entry,2)}
📊 Exit Price: {round(price,2)}

💸 Loss: ${round(loss_usd,2)}
📉 ROI: {round(loss_percent,2)}%""")

            positions = []
            base_price = price
            send(f"🔄 New Base: {round(base_price,2)}")

    time.sleep(CHECK_SPEED)
