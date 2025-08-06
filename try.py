import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Hardcoded user credentials (username:password)
USERS = {
    "1": "1",
    "2": "22"
}

# Function to authenticate user
def authenticate(username, password):
    return USERS.get(username) == password

# Function to get percentage change
def get_percentage_change(data):
    return data.pct_change() * 100

# Function to format volume with two decimal places
def format_volume(volume):
    if pd.isna(volume):
        return "N/A"
    elif volume >= 1_000_000:
        return f"{volume / 1_000_000:.2f}M"
    elif volume >= 1_000:
        return f"{volume / 1_000:.2f}K"
    else:
        return f"{volume:.2f}"

# Function to format values to two decimal places
def format_two_decimal(value):
    return f"{value:.2f}"

# Streamlit app
def main():
    st.title("DHAMELIYA AI STOCK DATA: SPECIFIED DATE AND LAST 5 DAYS")

    # User authentication
    st.sidebar.header("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login") or st.session_state.get('authenticated'):
        if authenticate(username, password) or st.session_state.get('authenticated'):
            st.session_state['authenticated'] = True
            st.sidebar.success("Logged in successfully!")

            # Input for multiple stock tickers
            tickers = st.text_input("Enter NSE Stock Tickers (comma-separated, e.g., FSL.NS, RELIANCE.NS):",
                                    "FSL.NS, RELIANCE.NS")

            # Input for the specified date (in DD/MM/YYYY format)
            input_date = st.date_input("Select Date", datetime.today()).strftime('%Y-%m-%d')

            if tickers:
                tickers_list = [ticker.strip() for ticker in tickers.split(',')]

                for ticker in tickers_list:
                    try:
                        st.write(f"Fetching data for {ticker}...")

                        # Calculate the date 6 days before the selected date to get the last 5 trading days
                        start_date = (datetime.strptime(input_date, '%Y-%m-%d') - timedelta(days=10)).strftime('%Y-%m-%d')

                        # Fetch historical data for the stock ticker
                        stock_data = yf.download(ticker, start=start_date, end=input_date, interval="1d")

                        if stock_data.empty:
                            st.warning(f"No data found for ticker: {ticker}")
                        else:
                            # Calculate percentage changes
                            stock_data['% Change'] = get_percentage_change(stock_data['Close'])

                            # Format volume and close price
                            stock_data['Volume'] = stock_data['Volume'].apply(format_volume)
                            stock_data['Close'] = stock_data['Close'].apply(format_two_decimal)
                            stock_data['% Change'] = stock_data['% Change'].apply(format_two_decimal)

                            # Sort data by date in descending order
                            sorted_data = stock_data.sort_index(ascending=False)

                            # Get the last 6 trading days including the specified date
                            last_6_days = sorted_data.head(6)

                            st.write(f"Data for {ticker} (Specified Date and Last 5 Trading Days):")
                            st.dataframe(last_6_days[['Close', 'Volume', '% Change']])

                    except Exception as e:
                        st.error(f"Error fetching data for ticker {ticker}: {str(e)}")

        else:
            st.sidebar.error("Invalid username or password")


if __name__ == "__main__":
    main()
