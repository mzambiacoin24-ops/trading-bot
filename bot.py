import os
import time
import requests

# ================= CONFIG =================
TOKEN = os.getenv("TOKEN")

SYMBOL = "BTC-USDT"
TRADE_AMOUNT = 10
MAX_BUYS = 5

TP_PERCENT = 0.002
SL_PERCENT = 0.003

CHECK_SPEED = 3

positions = []
base_price = None
CHAT_ID = None

# ================= TELEGRAM =================
def get_chat_id():
    global CHAT_ID
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        data = requests.get(url).json()
        if data["result"]:
            CHAT_ID = data["result"][-1]["message"]["chat"]["id"]
    except:
        pass

def send(msg):
    if not CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg}
        )
    except:
        pass

# ================= PRICE =================
def get_price():
    try:
        url = "https://api.kucoin.com/api/v1/market/orderbook/level1"
        params = {"symbol": SYMBOL}
        res = requests.get(url, params=params).json()
        return float(res["data"]["price"])
    except:
        return None

# ================= START =================
print("🚀 BOT STARTED")

# pata chat id mapema
while CHAT_ID is None:
    get_chat_id()
    print("Waiting for Telegram /start...")
    time.sleep(2)

send("🚀 GRID BOT ACTIVE")

# ================= MAIN =================
while True:
    price = get_price()
    if not price:
        time.sleep(CHECK_SPEED)
        continue

    print(f"Price: {price}")

    # ===== BASE =====
    if base_price is None:
        base_price = price
        send(f"📍 BASE: {round(base_price,2)}")

    # ===== BUY =====
    if len(positions) < MAX_BUYS and price <= base_price:
        positions.append({"price": price})

        if len(positions) == 1:
            total_capital = MAX_BUYS * TRADE_AMOUNT
            tp = price * (1 + TP_PERCENT)

            send(f"""📍 BASE: {round(base_price,2)}

💰 Total Capital (Grid): ${total_capital}

🎯 TP Target: {round(tp,2)}""")

        send(f"🟢 BUY {price}")

    # ===== TP SELL =====
    if positions:
        avg_entry = sum([p["price"] for p in positions]) / len(positions)
        tp_price = avg_entry * (1 + TP_PERCENT)

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

    # ===== STOP LOSS =====
    if positions:
        avg_entry = sum([p["price"] for p in positions]) / len(positions)
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
