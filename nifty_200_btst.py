import pandas as pd
import requests
import yfinance as yf

# ---------------------------------------------
# CONFIGURATION
# ---------------------------------------------

SEND_TELEGRAM = True  # Set True if you want alerts
BOT_TOKEN = "8578835344:AAHFnHTgi6S4hzhB0C-e_iwQFw302e-G2v8"
CHAT_ID = "933977274"

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
    "HDFCBANK.NS","RELIANCE.NS","ICICIBANK.NS","INFY.NS","BHARTIARTL.NS","LT.NS","SBIN.NS","ITC.NS","AXISBANK.NS","TCS.NS",
    "M&M.NS","KOTAKBANK.NS","BAJFINANCE.NS","MARUTI.NS","HINDUNILVR.NS","ETERNAL.NS","SUNPHARMA.NS","HCLTECH.NS","TITAN.NS",
    "NTPC.NS","BEL.NS","ULTRACEMCO.NS","TATASTEEL.NS","ASIANPAINT.NS","POWERGRID.NS","HINDALCO.NS","BAJAJFINSV.NS",
    "SHRIRAMFIN.NS","BSE.NS","ADANIPORTS.NS","INDIGO.NS","JSWSTEEL.NS","GRASIM.NS","TECHM.NS","BAJAJ-AUTO.NS","JIOFIN.NS",
    "EICHERMOT.NS","ONGC.NS","TRENT.NS","SBILIFE.NS","VEDL.NS","NESTLEIND.NS","COALINDIA.NS","TVSMOTOR.NS","CIPLA.NS",
    "HDFCLIFE.NS","MAXHEALTH.NS","HAL.NS","HEROMOTOCO.NS","DIVISLAB.NS","DRREDDY.NS","TATACONSUM.NS","WIPRO.NS","TMPV.NS",
    "CHOLAFIN.NS","APOLLOHOSP.NS","PERSISTENT.NS","BRITANNIA.NS","BPCL.NS","POLICYBZR.NS","COFORGE.NS","TATAPOWER.NS",
    "FEDERALBNK.NS","VBL.NS","SUZLON.NS","INDHOTEL.NS","IOC.NS","CUMMINSIND.NS","LTIM.NS","ADANIENT.NS","DMART.NS",
    "DIXON.NS","INDUSINDBK.NS","ADANIPOWER.NS","AUBANK.NS","INDUSTOWER.NS","NAUKRI.NS","BANKBARODA.NS","HDFCAMC.NS",
    "MOTHERSON.NS","LUPIN.NS","IDFCFIRSTB.NS","PFC.NS","PAYTM.NS","ICICIGI.NS","BAJAJHLDNG.NS","CANBK.NS","ASHOKLEY.NS",
    "GODREJCP.NS","FORTIS.NS","CGPOWER.NS","GAIL.NS","MFSL.NS","DLF.NS","PIDILITIND.NS","RECLTD.NS","YESBANK.NS",
    "HINDPETRO.NS","UNITDSPR.NS","UPL.NS","SRF.NS","MUTHOOTFIN.NS","PNB.NS","TORNTPHARM.NS","JINDALSTEL.NS","MARICO.NS",
    "HAVELLS.NS","GMRAIRPORT.NS","BHARATFORG.NS","POLYCAB.NS","NYKAA.NS","BHEL.NS","SHREECEM.NS","PHOENIXLTD.NS",
    "HYUNDAI.NS","MPHASIS.NS","AUROPHARMA.NS","AMBUJACEM.NS","SWIGGY.NS","ADANIENSOL.NS","LODHA.NS","MRF.NS",
    "ADANIGREEN.NS","SOLARINDS.NS","VOLTAS.NS","BOSCHLTD.NS","APLAPOLLO.NS","ALKEM.NS","GODREJPROP.NS","IDEA.NS",
    "UNIONBANK.NS","DABUR.NS","GLENMARK.NS","PRESTIGE.NS","COROMANDEL.NS","ABCAPITAL.NS","PIIND.NS","TIINDIA.NS",
    "COLPAL.NS","VMM.NS","SIEMENS.NS","WAAREEENER.NS","INDIANB.NS","ENRIN.NS","SBICARD.NS","ABB.NS","KEI.NS","NMDC.NS",
    "360ONE.NS","TORNTPOWER.NS","PAGEIND.NS","POWERINDIA.NS","M&MFIN.NS","NHPC.NS","MANKIND.NS","LTF.NS","JSWENERGY.NS",
    "NATIONALUM.NS","SUPREMEIND.NS","BLUESTARCO.NS","BIOCON.NS","JUBLFOOD.NS","ZYDUSLIFE.NS","OIL.NS","SONACOMS.NS",
    "HINDZINC.NS","KPITTECH.NS","IRFC.NS","IRCTC.NS","TATACOMM.NS","MAZDOCK.NS","KALYANKJIL.NS","ITCHOTELS.NS",
    "LICI.NS","OBEROIRLTY.NS","OFSS.NS","PATANJALI.NS","SAIL.NS","CONCOR.NS","EXIDEIND.NS","RVNL.NS","ASTRAL.NS",
    "TATAELXSI.NS","BANKINDIA.NS","ATGL.NS","LICHSGFIN.NS","IGL.NS","BDL.NS","COCHINSHIP.NS","BHARTIHEXA.NS",
    "MOTILALOFS.NS","ACC.NS","TATATECH.NS","IREDA.NS","GODFRYPHLP.NS","PREMIERENE.NS","HUDCO.NS","BAJAJHFL.NS",
    "NTPCGREEN.NS","IRB.NS"
]


print(f"Loaded {len(symbols)} NSE 200 symbols.\n")


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
            lines = ["📊 *Strong BTST Picks* (Score > 75) Nifty 200\n"]

            for idx, row in strong_df.iterrows():
                symbol = row["Symbol"]
                score = row["BTST Score"]
                current_price = row["Last Close"]
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
