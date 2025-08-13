import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import timedelta
import os

# Define valid usernames and passwords
USER_CREDENTIALS = {
    "1": "1",
    "22": "22"
}

def fetch_stock_data(symbol, start_date, end_date):
    """
    Fetch stock data from Yahoo Finance between start_date and end_date.
    """
    if pd.isnull(start_date) or pd.isnull(end_date):
        st.error(f"Invalid date range: Start Date: {start_date}, End Date: {end_date}")
        return pd.DataFrame()

    stock_data = yf.download(symbol, start=start_date, end=end_date)

    # Ensure the index is a DatetimeIndex
    stock_data.index = pd.to_datetime(stock_data.index)

    # Only keep weekdays (Mon-Fri)
    stock_data = stock_data[stock_data.index.dayofweek < 5]
    return stock_data

def process_data(df):
    all_results = {f'trading_day_{i + 1}': {'Yes': 0, 'No': 0, 'Highs': []} for i in range(10)}
    total_symbols = len(df)
    results = []

    for _, row in df.iterrows():
        symbol = row['symbol']
        date = row['date']

        if not pd.api.types.is_datetime64_any_dtype(type(date)):
            date = pd.to_datetime(date, dayfirst=True)

        previous_day = date - timedelta(days=1)

        stock_data = fetch_stock_data(symbol, previous_day - timedelta(days=10), date + timedelta(days=30))

        if not stock_data.empty and date in stock_data.index:
            try:
                closing_price = float(stock_data.loc[date]['Close'])
                current_day_high = float(stock_data.loc[date]['High'])

                # Find the previous trading day close
                previous_trading_day = stock_data.index[stock_data.index < date].max()
                if pd.notnull(previous_trading_day):
                    previous_close = float(stock_data.loc[previous_trading_day]['Close'])
                else:
                    previous_close = None

                # Calculate current day %
                if previous_close is not None and previous_close != 0:
                    current_day_pct = (closing_price - previous_close) / previous_close * 100
                else:
                    current_day_pct = None

                volume = float(stock_data.loc[date]['Volume']) if date in stock_data.index else None

                row_result = {
                    'symbol': symbol,
                    'date': date.strftime('%d-%m-%Y'),
                    'closing_price': f"{closing_price:.2f}",
                    'volume': f"{volume:.2f}" if volume is not None else None,
                    'current_day_high': f"{current_day_high:.2f}",
                    'current_day_%': f"{current_day_pct:.2f}" if current_day_pct is not None else None
                }

                # Process next 10 trading days
                future_trading_days = stock_data.index[stock_data.index > date][:10]

                for i, trading_day in enumerate(future_trading_days):
                    next_day_high = float(stock_data.loc[trading_day]['High'])
                    result = 'Yes' if closing_price * 1.01 <= next_day_high else 'No'
                    all_results[f'trading_day_{i + 1}'][result] += 1

                    row_result[f'trading_day_{i + 1}_date'] = trading_day.strftime('%d-%m-%Y')
                    row_result[f'trading_day_{i + 1}_high'] = f"{next_day_high:.2f}"
                    row_result[f'trading_day_{i + 1}_result'] = result

                    if result == 'Yes':
                        break

                results.append(row_result)

            except KeyError:
                results.append({**{
                    'symbol': symbol,
                    'date': date.strftime('%d-%m-%Y'),
                    'closing_price': None,
                    'volume': None,
                    'current_day_high': None,
                    'current_day_%': None
                }, **{f'trading_day_{i + 1}_date': None for i in range(10)},
                   **{f'trading_day_{i + 1}_high': None for i in range(10)},
                   **{f'trading_day_{i + 1}_result': 'None' for i in range(10)}})

    results_df = pd.DataFrame(results)

    remaining_no = total_symbols
    max_trading_day_yes = None
    for i in range(10):
        trading_day_index = f'trading_day_{i + 1}'
        remaining_no -= all_results[trading_day_index]['Yes']
        if remaining_no <= 0:
            max_trading_day_yes = i + 1
            break

    return results_df, all_results, max_trading_day_yes

def highlight_no_rows(row):
    return ['background-color: yellow' if 'No' in str(val) else '' for val in row]

def sidebar_login():
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.sidebar.success("Login successful!")
        else:
            st.sidebar.error("Invalid username or password. Please try again.")

def main():
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        sidebar_login()
    else:
        st.title("Dhameliya AI Data Processor")
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

        if uploaded_file is not None:
            uploaded_filename = os.path.splitext(uploaded_file.name)[0]
            df = pd.read_csv(uploaded_file, parse_dates=['date'], dayfirst=True)

            if df['date'].isnull().any():
                st.error("The CSV file contains invalid or missing dates.")
                return

            results_df, all_results, max_trading_day_yes = process_data(df)

            st.write("Processed Data:")
            st.dataframe(results_df.style.apply(highlight_no_rows, axis=1))

            if max_trading_day_yes:
                st.write(f"100% Yes results achieved on Trading Day {max_trading_day_yes}")
            else:
                st.write("100% Yes results not achieved within 10 trading days")

            for i in range(10):
                day_results = all_results[f'trading_day_{i + 1}']
                total_results = day_results['Yes'] + day_results['No']
                yes_percentage = (day_results['Yes'] / total_results * 100) if total_results > 0 else 0
                no_percentage = (day_results['No'] / total_results * 100) if total_results > 0 else 0

                st.write(f"Trading Day {i + 1}: Yes: {day_results['Yes']} ({yes_percentage:.2f}%), "
                         f"No: {day_results['No']} ({no_percentage:.2f}%)")

            csv = results_df.to_csv(index=False)
            st.download_button(
                label="Download results as CSV",
                data=csv,
                file_name=f"{uploaded_filename}_processed.csv",
                mime='text/csv'
            )

if __name__ == "__main__":
    main()
