import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="NSE OHLC Lookup", page_icon="📊")
st.title("📊 NSE Stock OHLC Lookup")

# Input: stock symbol and date
symbol = st.text_input("Enter NSE stock symbol (e.g. RELIANCE, TCS)", value="RELIANCE").strip().upper()
date = st.date_input("Select Date")

if st.button("Get OHLC Data"):
    ticker = symbol + ".NS"

    with st.spinner("Fetching data..."):
        # Download extra days to cover non-trading days
        start_date = date - pd.Timedelta(days=7)
        end_date = date + pd.Timedelta(days=1)
        df = yf.download(ticker, start=start_date, end=end_date)

    if df.empty:
        st.error(f"⚠️ No data found for {symbol} around {date}.")
    else:
        # Convert index to date only
        df.index = pd.to_datetime(df.index.date)
        
        if date in df.index:
            row = df.loc[date]
            st.success(f"✅ Data for {symbol} on {date}:")
        else:
            available_dates = df.index[df.index < date]
            if not available_dates.empty:
                closest_date = available_dates[-1]
                row = df.loc[closest_date]
                st.warning(f"⚠️ No data for {date}. Showing previous trading day: {closest_date}")
            else:
                st.error("⚠️ No previous trading days found.")
                st.stop()

        # Display OHLC
        st.subheader("📈 OHLC Data")
        st.dataframe(
            row[["Open", "High", "Low", "Close"]].round(2).to_frame().T
        )
