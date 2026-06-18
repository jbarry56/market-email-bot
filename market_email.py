
import os
import pandas as pd
import yfinance as yf
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

# =========================
# EMAIL SETTINGS (FROM GITHUB SECRETS)
# =========================

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# =========================
# WATCHLIST
# =========================

WATCHLIST = list(set([
"AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","TSLA",
"BRK-B","JPM","V","MA","LLY","UNH","XOM","WMT","COST",

"AVGO","AMD","INTC","QCOM","TXN","MU","AMAT","LRCX","KLAC","ADI","MCHP",
"SNPS","CDNS","PANW","CRWD","ZS","NET","DDOG","MDB","PLTR",
"ADBE","ORCL","NOW","CRM","INTU","TEAM","OKTA",
"NFLX","BKNG","CMCSA","TMUS","T","VZ",
"CSCO","PEP","KO","MDLZ","SBUX","MELI",
"ISRG","REGN","VRTX","AMGN","GILD","BIIB",
"HON","ADP","CTAS","ROP","FAST",
"EA","ABNB","ROKU",

"ASML","SNOW","SHOP","BX","KKR",
"PYPL","SQ",
"RKLB","LMT","NOC","RTX","BA",
"NEE","ENPH","ETN","DE","CAT",
"BABA","TCEHY","PDD","BYDDF","NIO",
"CQQQ","KWEB"
]))

# =========================
# DATA
# =========================

def get_data():

    rows = []

    for t in WATCHLIST:
        try:
            df = yf.Ticker(t).history(period="2y")
            if df is None or len(df) < 260:
                continue

            c = df["Close"].dropna()

            rows.append({
                "Ticker": t,
                "1D": (c.iloc[-1] / c.iloc[-2] - 1) * 100,
                "7D": (c.iloc[-1] / c.iloc[-8] - 1) * 100,
                "30D": (c.iloc[-1] / c.iloc[-31] - 1) * 100,
                "1Y": (c.iloc[-1] / c.iloc[-252] - 1) * 100,
            })

        except:
            continue

    return pd.DataFrame(rows)

# =========================
# COLOR FUNCTION
# =========================

def color(v):

    if v <= -3:
        return "background-color:#b30000"
    elif v <= -1:
        return "background-color:#ffb3b3"
    elif v <= 1:
        return "background-color:#f2f2f2"
    elif v <= 3:
        return "background-color:#b3ffb3"
    else:
        return "background-color:#1f7a1f"

# =========================
# BUILD HTML
# =========================

def build_html(df):

    html = "<h1>📊 Daily Market Heatmap</h1>"

    for col in ["1D","7D","30D","1Y"]:

        tmp = df.sort_values(col).copy()
        bottom = tmp.head(20)
        top = tmp.tail(20)

        table = pd.concat([bottom, top])

        html += f"<h2>{col} Movers</h2>"

        html += table.style \
            .applymap(color, subset=["1D","7D","30D","1Y"]) \
            .format("{:.2f}%") \
            .to_html()

    return html

# =========================
# SEND EMAIL
# =========================

def send_email(html):

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "📊 Daily Market Heatmap"
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_USER

    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, EMAIL_USER, msg.as_string())

# =========================
# RUN
# =========================

def main():

    df = get_data()
    html = build_html(df)
    send_email(html)
    print("Email sent")

if __name__ == "__main__":
    main()
