import os
import time
import random

# ==============================
# CONFIG (RAILWAY VARIABLES)
# ==============================
MODE = os.getenv("MODE", "paper")  # paper / live
TOKEN = os.getenv("TOKEN")

BASE_TP_PERCENT = 0.002  # 0.2%
MAX_BUYS = 5
GRID_SPACING = 50  # distance ya price
CAPITAL_PER_TRADE = 0.05  # 5%

# ==============================
# STATE
# ==============================
positions = []
base_price = None
tp_price = None
balance = 100  # paper balance

# ==============================
# MOCK PRICE (paper mode)
# ==============================
def get_price():
    return random.randint(79000, 80000)

# ==============================
# TREND ANALYSIS (simple)
# ==============================
def detect_trend():
    r = random.random()
    if r > 0.66:
        return "up"
    elif r < 0.33:
        return "down"
    return "sideways"

# ==============================
# CALCULATE AVERAGE PRICE
# ==============================
def average_price():
    if not positions:
        return 0
    return sum(p["price"] for p in positions) / len(positions)

# ==============================
# CALCULATE TP (dynamic)
# ==============================
def calculate_tp(avg, trend):
    if trend == "up":
        return avg * 1.0035
    elif trend == "down":
        return avg * 1.0015
    return avg * 1.002

# ==============================
# BUY LOGIC
# ==============================
def try_buy(price):
    global balance

    if len(positions) >= MAX_BUYS:
        return

    if not positions:
        positions.append({"price": price})
        print(f"🟢 BUY @ {price}")
        return

    last_price = positions[-1]["price"]

    if price <= last_price - GRID_SPACING:
        positions.append({"price": price})
        print(f"🟢 BUY @ {price}")

# ==============================
# SELL LOGIC
# ==============================
def try_sell(price):
    global positions, balance, base_price

    if not positions:
        return

    avg = average_price()
    trend = detect_trend()
    tp = calculate_tp(avg, trend)

    if price >= tp:
        total_invested = len(positions) * 10
        profit = total_invested * BASE_TP_PERCENT

        balance += profit

        print("\n🔴 SELL ALL EXECUTED")
        print(f"💰 Before: ${total_invested}")
        print(f"💰 After: ${total_invested + profit}")
        print(f"📈 Profit: +${round(profit,2)}\n")

        positions = []
        base_price = price

# ==============================
# MAIN LOOP
# ==============================
def run_bot():
    global base_price

    print("🚀 V7 BOT STARTED")

    while True:
        price = get_price()

        if base_price is None:
            base_price = price
            print(f"\n📍 BASE: {base_price}")

        print(f"Price: {price}")

        try_buy(price)
        try_sell(price)

        time.sleep(2)

# ==============================
# START
# ==============================
if __name__ == "__main__":
    run_bot()
