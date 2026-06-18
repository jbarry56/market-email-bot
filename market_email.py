import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd
import yfinance as yf


EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

if not EMAIL_USER or not EMAIL_PASS:
    raise ValueError("Missing EMAIL_USER or EMAIL_PASS GitHub secrets.")


WATCHLIST = sorted(set([
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
    "PYPL","XYZ",
    "RKLB","LMT","NOC","RTX","BA",
    "NEE","ENPH","ETN","DE","CAT",
    "BABA","TCEHY","PDD","BYDDF","NIO",
    "CQQQ","KWEB"
]))


def get_company_name(ticker: str, stock: yf.Ticker) -> str:
    try:
        info = stock.get_info()
        return info.get("shortName") or info.get("longName") or ticker
    except Exception:
        return ticker


def get_data() -> pd.DataFrame:
    rows = []

    for ticker in WATCHLIST:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2y", auto_adjust=True)

            if hist is None or hist.empty or "Close" not in hist.columns:
                print(f"Skipping {ticker}: no data")
                continue

            close = hist["Close"].dropna()

            if len(close) < 252:
                print(f"Skipping {ticker}: not enough history")
                continue

            p_now = close.iloc[-1]

            rows.append({
                "Ticker": ticker,
                "Company": get_company_name(ticker, stock),
                "1D": (p_now / close.iloc[-2] - 1) * 100,
                "7D": (p_now / close.iloc[-8] - 1) * 100,
                "30D": (p_now / close.iloc[-31] - 1) * 100,
                "1Y": (p_now / close.iloc[-252] - 1) * 100,
            })

        except Exception as e:
            print(f"Skipping {ticker}: {e}")

    if not rows:
        raise ValueError("No stock data loaded. Check yfinance availability.")

    df = pd.DataFrame(rows)
    return df.drop_duplicates("Ticker").reset_index(drop=True)


def cell_color(value: float) -> str:
    """
    Simple fixed bands:
    <= -3% dark red
    -3% to -1% light red
    -1% to +1% gray
    +1% to +3% light green
    > +3% dark green
    """
    if value <= -3:
        return "#cc3333"
    if value <= -1:
        return "#f4b6b6"
    if value <= 1:
        return "#eeeeee"
    if value <= 3:
        return "#b9e8b9"
    return "#2f8f46"


def format_pct(value: float) -> str:
    return f"{value:.2f}%"


def html_table(df: pd.DataFrame, metric: str) -> str:
    tmp = df.sort_values(metric, ascending=True).copy()
    table = pd.concat([tmp.head(20), tmp.tail(20)]).drop_duplicates("Ticker").reset_index(drop=True)

    cols = ["Ticker", "Company", "1D", "7D", "30D", "1Y"]

    html = """
    <table>
        <thead>
            <tr>
                <th>Ticker</th>
                <th>Company</th>
                <th>1D</th>
                <th>7D</th>
                <th>30D</th>
                <th>1Y</th>
            </tr>
        </thead>
        <tbody>
    """

    for _, row in table[cols].iterrows():
        html += "<tr>"
        html += f"<td><b>{row['Ticker']}</b></td>"
        html += f"<td>{row['Company']}</td>"

        for col in ["1D", "7D", "30D", "1Y"]:
            value = float(row[col])
            html += (
                f"<td style='background-color:{cell_color(value)};"
                f"text-align:center;font-weight:600;'>"
                f"{format_pct(value)}</td>"
            )

        html += "</tr>"

    html += """
        </tbody>
    </table>
    """

    return html


def build_html(df: pd.DataFrame) -> str:
    today = datetime.now().strftime("%Y-%m-%d")

    css = """
    <style>
        body {
            font-family: Arial, Helvetica, sans-serif;
            color: #111827;
            background-color: #ffffff;
        }
        h1 {
            font-size: 28px;
            margin-bottom: 4px;
        }
        h2 {
            font-size: 22px;
            margin-top: 28px;
            margin-bottom: 10px;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 6px;
        }
        .subtitle {
            color: #6b7280;
            margin-bottom: 20px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 18px;
            font-size: 14px;
        }
        th {
            background-color: #f3f4f6;
            border: 1px solid #d1d5db;
            padding: 8px;
            text-align: center;
            font-size: 15px;
        }
        td {
            border: 1px solid #d1d5db;
            padding: 7px;
        }
        td:nth-child(1) {
            text-align: center;
            width: 80px;
        }
        td:nth-child(2) {
            min-width: 220px;
        }
    </style>
    """

    html = f"""
    <html>
    <head>{css}</head>
    <body>
        <h1>Daily Market Heatmap</h1>
        <div class="subtitle">Generated {today}. Universe: {len(df)} valid tickers.</div>

        <h2>1D Movers: Bottom 20 + Top 20</h2>
        {html_table(df, "1D")}

        <h2>7D Movers: Bottom 20 + Top 20</h2>
        {html_table(df, "7D")}

        <h2>30D Movers: Bottom 20 + Top 20</h2>
        {html_table(df, "30D")}

        <h2>1Y Movers: Bottom 20 + Top 20</h2>
        {html_table(df, "1Y")}
    </body>
    </html>
    """

    return html


def send_email(html: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Daily Market Heatmap"
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_USER

    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, EMAIL_USER, msg.as_string())


def main() -> None:
    df = get_data()
    html = build_html(df)
    send_email(html)
    print("Email sent successfully.")


if __name__ == "__main__":
    main()
