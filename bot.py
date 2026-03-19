import asyncio
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "WEKA_TOKEN_HAPA"
CHAT_ID = None

SYMBOL = "BTC-USDT"

CHECK_SPEED = 2
MAX_BUYS = 5

active_buys = []
total_profit = 0
base = 0


def get_price():
    try:
        url = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={SYMBOL}"
        res = requests.get(url).json()
        return float(res['data']['price'])
    except:
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHAT_ID
    CHAT_ID = update.effective_chat.id
    await update.message.reply_text("🚀 GRID V6 ACTIVE")


async def run_bot(app):
    global base, active_buys, total_profit

    while True:
        price = get_price()

        if price is None or CHAT_ID is None:
            await asyncio.sleep(CHECK_SPEED)
            continue

        # SET BASE
        if base == 0:
            base = price
            await app.bot.send_message(chat_id=CHAT_ID, text=f"📊 Base: {base}")
            await asyncio.sleep(CHECK_SPEED)
            continue

        # BUY
        if price < base and len(active_buys) < MAX_BUYS:
            active_buys.append(price)
            await app.bot.send_message(chat_id=CHAT_ID, text=f"🟢 BUY {price}")

        # SELL ALL
        if active_buys:
            avg = sum(active_buys) / len(active_buys)
            profit = ((price - avg) / avg) * 100

            if profit >= 0.05:
                total_profit += profit

                await app.bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"🔴 SELL {price}\nProfit: {round(profit,4)}%\nTotal: {round(total_profit,4)}%"
                )

                active_buys = []
                base = price

                await app.bot.send_message(chat_id=CHAT_ID, text=f"🔄 New Base: {base}")

        await asyncio.sleep(CHECK_SPEED)


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # HII NDIO FIX YA ERROR YAKO 🔥
    app.job_queue.run_repeating(lambda *_: asyncio.create_task(run_bot(app)), interval=1, first=1)

    print("✅ BOT RUNNING...")
    app.run_polling()


if __name__ == "__main__":
    main()
