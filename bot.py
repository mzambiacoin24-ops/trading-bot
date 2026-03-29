import os
import time
import requests

# ================= CONFIG =================
TOKEN = os.getenv("TOKEN")

COINS = ["BTC-USDT", "ETH-USDT", "SOL-USDT", "XRP-USDT"]

TRADE_AMOUNT = 10
MAX_BUYS = 5

TP_PERCENT = 0.007     # 0.7% (profit kubwa)
SL_PERCENT = 0.02      # 2% (balanced)

GRID_STEP = 80         # spacing kubwa (no overtrading)
CHECK_SPEED = 3

# ================= STATE =================
positions = []
entry_prices = []
CHAT_ID = None
active_symbol = None
in_trade = False

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

# ================= PICK COIN =================
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
print("🚀 V7 STARTED")

while CHAT_ID is None:
    get_chat_id()
    time.sleep(2)

send("🚀 GRID V7 ACTIVE")

# ================= MAIN =================
while True:

    # ===== COLLECT PRICES =====
    for coin in COINS:
        price = get_price(coin)
        if price:
            price_data[coin].append(price)
            if len(price_data[coin]) > 20:
                price_data[coin].pop(0)

    # ===== CHOOSE COIN =====
    if not in_trade:
        active_symbol = pick_best_coin()

    if not active_symbol:
        time.sleep(CHECK_SPEED)
        continue

    price = price_data[active_symbol][-1]
    trend = detect_trend(price_data[active_symbol])

    # ================= SMART ENTRY =================
    if not in_trade and trend == "DOWN":
        in_trade = True
        positions = []
        entry_prices = []
        base_price = price

        send(f"📍 {active_symbol} (SMART ENTRY)\n📊 Base: {round(base_price,2)}")

    # ================= GRID BUY (STEP BY STEP) =================
    if in_trade and len(positions) < MAX_BUYS:
        next_buy = base_price - (len(positions) * GRID_STEP)

        if price <= next_buy:
            positions.append(next_buy)
            entry_prices.append(next_buy)
            send(f"🟢 BUY {round(next_buy,2)}")

    # ================= TAKE PROFIT =================
    if in_trade and positions:
        avg = sum(entry_prices) / len(entry_prices)
        tp_price = avg * (1 + TP_PERCENT)

        if price >= tp_price:
            capital = len(entry_prices) * TRADE_AMOUNT
            profit = capital * ((price - avg) / avg)

            send(f"""📤 TP HIT

🪙 {active_symbol}
💰 Capital: ${capital}
📊 Avg: {round(avg,2)}
📊 Exit: {round(price,2)}

💵 Profit: ${round(profit,2)}""")

            positions = []
            entry_prices = []
            in_trade = False
            active_symbol = None

    # ================= STOP LOSS =================
    if in_trade and entry_prices:
        avg = sum(entry_prices) / len(entry_prices)
        sl = avg * (1 - SL_PERCENT)

        if price <= sl:
            capital = len(entry_prices) * TRADE_AMOUNT
            loss = capital * ((price - avg) / avg)

            send(f"""🛑 STOP LOSS

🪙 {active_symbol}
💰 Capital: ${capital}
📉 Loss: ${round(loss,2)}""")

            positions = []
            entry_prices = []
            in_trade = False
            active_symbol = None

    # ================= MARKET WATCH =================
    msg = "📊 Market:\n"
    for coin in COINS:
        if price_data[coin]:
            msg += f"{coin}: {round(price_data[coin][-1],2)}\n"

    market_watch(msg)

    time.sleep(CHECK_SPEED)
