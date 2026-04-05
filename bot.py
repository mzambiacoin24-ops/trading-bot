import os
import time
import requests

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = None

def send(msg):
    global CHAT_ID
    if CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg})

def get_chat_id():
    global CHAT_ID
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    try:
        data = requests.get(url).json()
        print(data)
        if data.get("result"):
            CHAT_ID = data["result"][-1]["message"]["chat"]["id"]
            print("CHAT_ID:", CHAT_ID)
    except Exception as e:
        print("ERROR:", e)

print("🚀 BOT STARTING...")

while True:
    try:
        get_chat_id()

        if CHAT_ID:
            send("🔥 BOT WORKING NOW")

        time.sleep(5)

    except Exception as e:
        print("MAIN ERROR:", e)
        time.sleep(5)
