import time
import requests
import pandas as pd
from kiteconnect import KiteConnect
from datetime import datetime, timedelta, time as dtime
import os


API_KEY = os.environ.get("KITE_API_KEY")
ACCESS_TOKEN = os.environ.get("KITE_ACCESS_TOKEN")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

LIVE_TRADING = False   # 🔴 True = REAL MONEY

kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

# ================= CONFIG =================
SYMBOLS = [
    "360ONE", "AIAENG", "AARTIIND", "ANGELONE", "APOLLOTYRE", "ARVIND",
    "BALRAMCHIN", "BRIGADE", "CEATLTD", "GHCL", "GPIL", "GRAPHITE", "GNFC",
    "GSFC", "HONASA", "INDIAMART", "ICIL", "IGIL", "JSL", "KPRMILL", "KPIL",
    "KKCL", "MCX", "NOCIL", "PHOENIXLTD", "RATEGAIN", "SYNGENE", "UTIAMC",
    "SOBHA", "ASTRAZEN", "PRICOLLTD", "RATNAMANI", "GVT&D", "BLACKBUCK",
    "AVANTIFEED", "ELGIEQUIP", "INDIACEM", "VARROC", "CARERATING", "NYKAA"
]

CAPITAL = 120000
MAX_LOSS = 1000
RR = 1.1
VOLUME_MULT = 1.2

# ================= TELEGRAM =================
def send_telegram(msg):
    print(msg)
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})

# ================= HELPERS =================
def get_tokens(symbols):
    inst = pd.DataFrame(kite.instruments("NSE"))
    inst = inst[inst["tradingsymbol"].isin(symbols)]
    return dict(zip(inst["tradingsymbol"], inst["instrument_token"]))

def get_intraday(token):
    data = kite.historical_data(
        instrument_token=token,
        from_date=datetime.now().date(),
        to_date=datetime.now(),
        interval="5minute"
    )

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # --- FORCE datetime index ---
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df.set_index("date", inplace=True)
    else:
        df.index = pd.to_datetime(df.index, errors="coerce")

    # --- DROP bad rows ---
    df = df[~df.index.isna()]

    # --- ENSURE DatetimeIndex ---
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    return df


def wait_for_order_complete(order_id, timeout=20):
    """Wait until order is COMPLETE or FAILED"""
    start = time.time()
    while time.time() - start < timeout:
        for o in kite.orders():
            if o["order_id"] == order_id:
                if o["status"] == "COMPLETE":
                    return True
                if o["status"] in ["REJECTED", "CANCELLED"]:
                    return False
        time.sleep(1)
    return False

# ================= WAIT FOR 9:35 =================
while datetime.now().time() < dtime(9, 36):
    time.sleep(5)

# ================= SIGNAL GENERATION =================
tokens = get_tokens(SYMBOLS)
candidates = []

for symbol, token in tokens.items():
    df = get_intraday(token)

    if df.empty:
        continue

    df = df.between_time("09:15", "15:30")

    OR = df.between_time("9:15", "9:30")
    if OR.empty:
        continue

    OR_high = OR["high"].max()
    OR_low = OR["low"].min()
    OR_vol = OR["volume"].mean()
    OR_range = OR_high - OR_low

    candle = df[df.index.time == dtime(9, 35)]
    if candle.empty:
        continue

    row = candle.iloc[0]
    entry = sl = target = qty = side = None
    score = 0

    # -------- SELL --------
    if row["high"] > OR_high and row["volume"] > OR_vol * VOLUME_MULT:
        entry = row["high"]
        sl = entry * 1.005
        risk = sl - entry
        qty = int(min(CAPITAL / entry, MAX_LOSS / risk))
        target = entry - (risk * RR) - (OR_range * 0.2)
        side = "SELL"
        score = OR_range + (row["high"] - OR_high)

    # -------- BUY --------
    if row["low"] < OR_low and row["volume"] > OR_vol * VOLUME_MULT:
        entry = row["low"]
        sl = entry * 0.995
        risk = entry - sl
        qty = int(min(CAPITAL / entry, MAX_LOSS / risk))
        target = entry + (risk * RR) + (OR_range * 0.2)
        side = "BUY"
        score = OR_range + (OR_low - row["low"])

    if side and qty > 0:
        candidates.append({
            "symbol": symbol,
            "side": side,
            "entry": round(entry, 2),
            "sl": round(sl, 2),
            "target": round(target, 2),
            "qty": qty,
            "score": score
        })

# ================= TELEGRAM ALERT =================
if not candidates:
    send_telegram("❌ ORB 9:35\nNo valid stock today.")
    exit()

top_trades = sorted(candidates, key=lambda x: x["score"], reverse=True)[:2]

msg = "📊 ORB 9:35 (SAFE GTT)\n\n"
for t in top_trades:
    msg += (
        f"{t['symbol']} | {t['side']}\n"
        f"Entry: {t['entry']} | SL: {t['sl']} | Target: {t['target']}\n"
        f"Qty: {t['qty']}\n\n"
    )
msg += "🔴 LIVE MODE" if LIVE_TRADING else "🟡 PAPER MODE"
print(msg)
send_telegram(msg)

# ================= PLACE ORDERS =================
if not LIVE_TRADING:
    print("🟡 PAPER MODE — No orders placed")
    exit()

for t in top_trades:
    order_id = kite.place_order(
        variety=kite.VARIETY_REGULAR,
        exchange=kite.EXCHANGE_NSE,
        tradingsymbol=t["symbol"],
        transaction_type=(
            kite.TRANSACTION_TYPE_BUY if t["side"] == "BUY"
            else kite.TRANSACTION_TYPE_SELL
        ),
        quantity=t["qty"],
        product=kite.PRODUCT_MIS,
        order_type=kite.ORDER_TYPE_MARKET
    )

    # ✅ WAIT FOR CONFIRMATION
    filled = wait_for_order_complete(order_id)

    if not filled:
        send_telegram(f"❌ ENTRY FAILED — {t['symbol']} | GTT NOT PLACED")
        continue

    # ✅ PLACE GTT ONLY AFTER ENTRY CONFIRM
    kite.place_gtt(
        trigger_type=kite.GTT_TYPE_OCO,
        tradingsymbol=t["symbol"],
        exchange=kite.EXCHANGE_NSE,
        trigger_values=[t["sl"], t["target"]],
        last_price=t["entry"],
        orders=[
            {
                "transaction_type": (
                    kite.TRANSACTION_TYPE_SELL if t["side"] == "BUY"
                    else kite.TRANSACTION_TYPE_BUY
                ),
                "quantity": t["qty"],
                "product": kite.PRODUCT_MIS,
                "order_type": kite.ORDER_TYPE_MARKET
            },
            {
                "transaction_type": (
                    kite.TRANSACTION_TYPE_SELL if t["side"] == "BUY"
                    else kite.TRANSACTION_TYPE_BUY
                ),
                "quantity": t["qty"],
                "product": kite.PRODUCT_MIS,
                "order_type": kite.ORDER_TYPE_MARKET
            }
        ]
    )

    send_telegram(f"✅ ENTRY CONFIRMED + GTT SET — {t['symbol']}")

#send_telegram("🏁 ORB Execution Completed")
