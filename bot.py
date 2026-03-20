import os
import time
import requests

# ================= CONFIG =================
TOKEN = os.getenv("TOKEN")

COINS = ["BTC-USDT", "ETH-USDT", "SOL-USDT", "XRP-USDT"]

TRADE_AMOUNT = 10
MAX_BUYS = 5

TP_PERCENT = 0.002
SL_PERCENT = 0.003

GRID_SPACING = 20
CHECK_SPEED = 3

# ================= STATE =================
positions = []
base_price = None
CHAT_ID = None
active_symbol = None

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
def detect_trend(history):
    if len(history) < 5:
        return "SIDE"
    if history[-1] > history[-5]:
        return "UP"
    elif history[-1] < history[-5]:
        return "DOWN"
    return "SIDE"

# ================= BEST COIN =================
def pick_best_coin():
    best = None
    best_move = 0

    for coin in COINS:
        h = price_data[coin]
        if len(h) < 5:
            continue

        move = abs(h[-1] - h[-5])

        if move > best_move:
            best_move = move
            best = coin

    return best

# ================= START =================
print("🚀 V9 STARTED")

while CHAT_ID is None:
    get_chat_id()
    time.sleep(2)

send("🚀 GRID V9 ACTIVE")

# ================= MAIN =================
while True:

    # ===== COLLECT DATA =====
    for coin in COINS:
        price = get_price(coin)
        if price:
            price_data[coin].append(price)
            if len(price_data[coin]) > 20:
                price_data[coin].pop(0)

    # ===== PICK COIN =====
    if active_symbol is None:
        active_symbol = pick_best_coin()
        if active_symbol:
            send(f"🔥 Selected: {active_symbol}")

    if not active_symbol:
        time.sleep(CHECK_SPEED)
        continue

    price = price_data[active_symbol][-1]
    trend = detect_trend(price_data[active_symbol])

    if base_price is None:
        base_price = price

    # ================= BUY =================
    if len(positions) < MAX_BUYS and trend != "DOWN":

        if not positions and price <= base_price:
            positions.append(price)

            total_capital = MAX_BUYS * TRADE_AMOUNT
            tp = price * (1 + TP_PERCENT)

            send(f"""📍 {active_symbol}

💰 Capital: ${total_capital}
🎯 TP: {round(tp,2)}

🟢 BUY {round(price,2)}""")

        elif positions:
            last_buy = positions[-1]

            if price <= last_buy - GRID_SPACING:
                positions.append(price)
                send(f"🟢 BUY {round(price,2)}")

    # ================= SELL =================
    if positions:
        avg = sum(positions) / len(positions)
        tp_price = avg * (1 + TP_PERCENT)

        if price >= tp_price:
            capital = len(positions) * TRADE_AMOUNT
            profit = capital * ((price - avg) / avg)

            send(f"""📤 TRADE CLOSED

🪙 {active_symbol}
💰 Capital: ${capital}
📊 Entries: {len(positions)}
📊 Avg Entry: {round(avg,2)}
📊 Exit: {round(price,2)}

💵 Profit: ${round(profit,2)}""")

            positions = []
            base_price = price
            active_symbol = None

    # ================= STOP LOSS =================
    if positions:
        avg = sum(positions) / len(positions)
        sl = avg * (1 - SL_PERCENT)

        if price <= sl:
            capital = len(positions) * TRADE_AMOUNT
            loss = capital * ((price - avg) / avg)

            send(f"""🛑 STOP LOSS

🪙 {active_symbol}
💰 Capital: ${capital}
📉 Loss: ${round(loss,2)}""")

            positions = []
            base_price = price
            active_symbol = None

    # ================= MARKET WATCH =================
    msg = "📊 Market Watch (Live):\n"
    for coin in COINS:
        if price_data[coin]:
            p = price_data[coin][-1]
            msg += f"{coin}: {round(p,2)}\n"

    market_watch(msg)

    time.sleep(CHECK_SPEED)
