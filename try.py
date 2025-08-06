import streamlit as st
import yfinance as yf
import pandas as pd

st.title("📊 NSE Stock OHLC Lookup")

symbol = st.text_input("Enter NSE stock symbol (e.g. RELIANCE, TCS)", value="RELIANCE").upper()
date = st.date_input("Select Date")

if st.button("Get OHLC Data"):
    ticker = symbol + ".NS"
    # Download past 10 days to find closest trading day if selected one fails
    df = yf.download(ticker, start=date - pd.Timedelta(days=7), end=date + pd.Timedelta(days=1))

    if df.empty:
        st.error(f"No data found for {symbol} around {date}.")
    else:
        # Try to get exact date match
        if str(date) in df.index.strftime('%Y-%m-%d'):
            row = df.loc[str(date)]
            st.success(f"Data for {symbol} on {date}:")
        else:
            # Use the last available date before the selected one
            available_dates = df.index[df.index < pd.to_datetime(date)]
            if not available_dates.empty:
                closest_date = available_dates[-1]
                row = df.loc[closest_date]
                st.warning(f"No data for {date}. Showing data from previous trading day: {closest_date.date()}")
            else:
                st.error("No trading days found before selected date.")
                st.stop()

        st.write({
            "Open": round(row["Open"], 2),
            "High": round(row["High"], 2),
            "Low": round(row["Low"], 2),
            "Close": round(row["Close"], 2),
        })
