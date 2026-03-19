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

GRID_SPACING = 20
CHECK_SPEED = 3
BUY_COOLDOWN = 10

# ================= STATE =================
positions = []
base_price = None
last_buy_time = 0
in_trade = False

CHAT_ID = None
bot_started = False

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

while CHAT_ID is None:
    get_chat_id()
    time.sleep(2)

# ================= MAIN =================
while True:
    price = get_price()
    if not price:
        time.sleep(CHECK_SPEED)
        continue

    print("Price:", price)

    # START MESSAGE (once)
    if not bot_started:
        send("🚀 GRID BOT ACTIVE")
        bot_started = True

    # SET BASE
    if base_price is None:
        base_price = price

    current_time = time.time()

    # ================= BUY =================
    if len(positions) < MAX_BUYS and (current_time - last_buy_time > BUY_COOLDOWN):

        if not positions:
            if price <= base_price:
                positions.append(price)
                last_buy_time = current_time
                in_trade = True

                total_capital = MAX_BUYS * TRADE_AMOUNT
                tp = price * (1 + TP_PERCENT)

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
            in_trade = False

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
            in_trade = False

            send(f"🔄 New Base: {round(base_price,2)}")

    time.sleep(CHECK_SPEED)
