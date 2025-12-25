import pandas as pd
import requests
import yfinance as yf
import os

# ---------------------------------------------
# CONFIGURATION
# ---------------------------------------------

SEND_TELEGRAM = True  # Set True if you want alerts
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(msg):
    if SEND_TELEGRAM:
        print("Sending email:")
        requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            params={"chat_id": CHAT_ID, "text": msg}
        )
# ---------------------------------------------
# STEP 1: GET NSE-200 STOCK LIST AUTOMATICALLY
# ---------------------------------------------


symbols = [
    "360ONE.NS","AIAENG.NS","AARTIIND.NS","ANGELONE.NS","APOLLOTYRE.NS",
    "ARVIND.NS","BALRAMCHIN.NS","BRIGADE.NS","CEATLTD.NS","GHCL.NS","GPIL.NS",
    "GRAPHITE.NS","GNFC.NS","GSFC.NS","HONASA.NS","INDIAMART.NS","ICIL.NS",
    "IGIL.NS","JSL.NS","KPRMILL.NS","KPIL.NS","KKCL.NS","MCX.NS","NOCIL.NS",
    "PHOENIXLTD.NS","RATEGAIN.NS","SYNGENE.NS","UTIAMC.NS","SOBHA.NS",
    "ASTRAZEN.NS","PRICOLLTD.NS","RATNAMANI.NS","GVT&D.NS","BLACKBUCK.NS",
    "AVANTIFEED.NS","ELGIEQUIP.NS","INDIACEM.NS","VARROC.NS","CARERATING.NS","NYKAA.NS"
    # Add Nifty 200 or any list of stocks you want
]

print(f"Loaded {len(symbols)} NSE symbols.\n")


# ---------------------------------------------
# STEP 2: BTST CALCULATION FUNCTION
# ---------------------------------------------

def btst_check(symbol):
    try:
        ticker = yf.Ticker(symbol)

        # 1-year historical data for trend & volume
        hist = ticker.history(period="1y")
        if hist.empty:
            return None

        # Today 5-minute intraday candles
        intraday = ticker.history(interval="5m", period="1d")
        if intraday.empty:
            return None

        # 20DMA, 50DMA
        ma20 = hist["Close"].rolling(20).mean().iloc[-1]
        ma50 = hist["Close"].rolling(50).mean().iloc[-1]

        prev_high = hist["High"].iloc[-2]

        # Today's high, close
        today_high = intraday["High"].max()
        today_close = intraday["Close"].iloc[-1]

        # 3PM (last candle)
        last_candle = intraday.iloc[-1]
        lc_open = last_candle["Open"]
        lc_close = last_candle["Close"]
        lc_high = last_candle["High"]

        avg_vol_10 = hist["Volume"].rolling(10).mean().iloc[-1]
        today_vol = intraday["Volume"].sum()

        # Conditions
        cond_breakout = today_high > prev_high
        cond_above_20dma = today_close > ma20
        cond_above_50dma = today_close > ma50
        cond_volume = today_vol > (1.5 * avg_vol_10)
        cond_strong_close = lc_close > (0.9 * lc_high)

        # Risk-adjusted BTST score (0–100)
        score = (
            25 * cond_breakout +
            20 * cond_above_20dma +
            15 * cond_above_50dma +
            20 * cond_volume +
            20 * cond_strong_close
        )

        if score < 60:
            return None

        return {
            "Symbol": symbol,
            "Last Close": today_close,
            "Breakout > Prev High": cond_breakout,
            "Above 20 DMA": cond_above_20dma,
            "Above 50 DMA": cond_above_50dma,
            "Volume Surge": cond_volume,
            "Strong 3PM Candle": cond_strong_close,
            "BTST Score": score
        }

    except Exception as e:
        print(f"Error in {symbol}: {e}")
        return None


# ---------------------------------------------
# STEP 3: RUN SCANNER
# ---------------------------------------------

print("Scanning for BTST opportunities...\n")

btst_results = []

for sym in symbols:
    result = btst_check(sym)
    if result:
        btst_results.append(result)
        print(f"BTST Candidate → {sym} (Score: {result['BTST Score']})")

# Convert to DataFrame
df = pd.DataFrame(btst_results)

# If no candidates at all
if df.empty:
    if SEND_TELEGRAM:
        send_telegram("No BTST candidates found today.")
    print("\nNo BTST candidates found.")
else:
    # Filter only strong picks (Score > 75)
    strong_df = df[df["BTST Score"] > 75].sort_values("BTST Score", ascending=False)

    # Only send Telegram if strong candidates exist
    if SEND_TELEGRAM:
        if strong_df.empty:
            send_telegram("No strong BTST candidates today (Score > 75).")
        else:
            lines = ["📊 *Strong BTST Picks* (Score > 75) PMS\n"]

            for idx, row in strong_df.iterrows():
                symbol = row["Symbol"]
                score = row["BTST Score"]
                current_price= row["Last Close"]
                lines.append(f"• {symbol} — Score: {score} - Current Price: {current_price}")

            final_msg = "\n".join(lines)
            send_telegram(final_msg.replace("*", ""))  # avoid markdown issues

    print("\nStrong BTST candidates:")
    if not strong_df.empty:
        print(strong_df)
    else:
        print("None with Score > 75")

# # ---------------------------------------------
# # STEP 4: SAVE RESULTS
# # ---------------------------------------------
#
# df = pd.DataFrame(btst_results)
# df = df.sort_values("BTST Score", ascending=False)
#
# df.to_csv("btst_scanner_results.csv", index=False)
#
# print("\nScan complete!")
# print(f"Total BTST Candidates: {len(df)}")
# print("\nSaved → btst_scanner_results.csv")
#
# if len(df) > 0:
#     print(df.head())
