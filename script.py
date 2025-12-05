import datetime
import requests

SEND_TELEGRAM = True  # Set True if you want alerts
BOT_TOKEN = "8578835344:AAHFnHTgi6S4hzhB0C-e_iwQFw302e-G2v8"
CHAT_ID = "933977274"

def send_telegram(msg):
    if SEND_TELEGRAM:
        requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            params={"chat_id": CHAT_ID, "text": msg}
        )

send_telegram("Akshay")

def main():
    print("Running scheduled job at:", datetime.datetime.utcnow())


if __name__ == "__main__":
    main()
    send_telegram("Test from github")