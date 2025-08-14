import yfinance as yf
import pandas as pd
import streamlit as st
import time
import datetime

# -------------------------------
# Thresholds based on price ranges
# -------------------------------
ranges = {
    (0, 200): 0.20,
    (200, 500): 0.70,
    (500, 1000): 1.00,
    (1000, 2000): 2.00,
    (2000, 3000): 3.00,
    (3000, 4000): 4.00,
    (4000, 5000): 5.00,
    (5000, 8000): 5.00
}

# -------------------------------
# Find highs within threshold
# -------------------------------
def find_high_difference(data, threshold, current_close):
    highs = data['High'].values
    dates = data.index
    high_pairs = []

    for i in range(len(highs)):
        for j in range(i + 1, len(highs)):
            high1, date1 = highs[i], dates[i]
            high2, date2 = highs[j], dates[j]
            diff = abs(high1 - high2)

            if diff <= threshold and current_close > max(high1, high2):
                high_pairs.append({
                    'difference': diff,
                    'high1': high1,
                    'date1': date1.strftime("%Y-%m-%d"),
                    'high2': high2,
                    'date2': date2.strftime("%Y-%m-%d")
                })
    return high_pairs

# -------------------------------
# Get threshold for given price
# -------------------------------
def get_threshold(close_price):
    for price_range, threshold in ranges.items():
        if price_range[0] <= close_price < price_range[1]:
            return threshold
    return None

# -------------------------------
# Analyze a single stock
# -------------------------------
def analyze_stock(symbol, price_range, custom_date=None):
    try:
        if custom_date:
            end_date = pd.to_datetime(custom_date)
        else:
            end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=30)

        data = yf.download(symbol, start=start_date, end=end_date + datetime.timedelta(days=1), interval="1d").dropna()

        if data.empty or len(data) < 11:
            return [], None, None, None, None, [], [], []

        last_11_days = data.tail(11)
        last_10_days = last_11_days.head(10).sort_index(ascending=False)

        previous_dates = last_10_days.index.strftime("%Y-%m-%d").tolist()

        if 'Close' not in last_10_days.columns or 'High' not in last_10_days.columns:
            return [], None, None, None, None, [], [], []

        previous_closes = last_10_days['Close'].squeeze()
        previous_highs = last_10_days['High'].squeeze()

        previous_closes = previous_closes.tolist() if hasattr(previous_closes, "tolist") else list(previous_closes)
        previous_highs = previous_highs.tolist() if hasattr(previous_highs, "tolist") else list(previous_highs)

        current_close = float(data['Close'].iloc[-1])
        current_volume = float(data['Volume'].iloc[-1])
        current_high = float(data['High'].iloc[-1])
        current_date = data.index[-1].strftime("%Y-%m-%d")

        threshold = get_threshold(current_close)

        if price_range and not (price_range[0] <= current_close < price_range[1]):
            return [], current_close, current_volume, current_date, current_high, previous_dates, previous_closes, previous_highs

        if threshold is not None:
            high_pairs = find_high_difference(last_10_days, threshold, current_close)
            return high_pairs, current_close, current_volume, current_date, current_high, previous_dates, previous_closes, previous_highs

        return [], current_close, current_volume, current_date, current_high, previous_dates, previous_closes, previous_highs

    except Exception as e:
        return f"Error: {e}", None, None, None, None, [], [], []

# -------------------------------
# Analyze multiple stocks in batches
# -------------------------------
def analyze_stocks_in_batches(symbols, price_range=None, batch_size=100, log_placeholder=None, custom_date=None):
    results = []
    total_symbols = len(symbols)

    for start_idx in range(0, total_symbols, batch_size):
        batch_symbols = symbols[start_idx:start_idx + batch_size]

        for idx, symbol in enumerate(batch_symbols, start=start_idx + 1):
            log_text = f"[{idx}/{total_symbols}] Processing: {symbol} ..."
            if log_placeholder:
                log_placeholder.text(log_text)

            result = analyze_stock(symbol, price_range, custom_date)
            if len(result) != 8:
                results.append({"Stock": symbol, "Error": "Invalid result structure"})
                continue

            high_pairs, current_close, current_volume, current_date, current_high, prev_dates, prev_closes, prev_highs = result

            if isinstance(high_pairs, str) and high_pairs.startswith("Error:"):
                results.append({"Stock": symbol, "Error": high_pairs})
                continue

            if high_pairs:
                for pair in high_pairs:
                    row = {
                        "Stock": symbol,
                        "High Difference": f"{float(pair['difference']):.2f}",
                        "Date 1": pair['date1'],
                        "High 1": f"{float(pair['high1']):.2f}",
                        "Date 2": pair['date2'],
                        "High 2": f"{float(pair['high2']):.2f}",
                        "Current Date": current_date,
                        "Current High": f"{float(current_high):.2f}",
                        "Current Close Price": f"{float(current_close):.2f}",
                        "Current Volume": f"{float(current_volume):.2f}"
                    }
                    for i in range(10):
                        row[f"Prev Date {i+1}"] = prev_dates[i] if i < len(prev_dates) else ""
                        row[f"Prev Close {i+1}"] = f"{float(prev_closes[i]):.2f}" if i < len(prev_closes) else ""
                        row[f"Prev High {i+1}"] = f"{float(prev_highs[i]):.2f}" if i < len(prev_highs) else ""
                    results.append(row)
                log_placeholder.text(f"[{idx}/{total_symbols}] ✅ Passed: {symbol}")
            else:
                log_placeholder.text(f"[{idx}/{total_symbols}] ❌ No match: {symbol}")

        time.sleep(5)

    return results

# -------------------------------
# Post-processing filter
# -------------------------------
def process_data(df):
    results = []
    for _, row in df.iterrows():
        try:
            current_date = pd.to_datetime(row['Current Date'], errors='coerce')
            if pd.isna(current_date):
                continue

            prev_dates = [pd.to_datetime(row[f'Prev Date {i}'], errors='coerce') for i in range(1, 11)]
            prev_closes = [row[f'Prev Close {i}'] for i in range(1, 11)]
            prev_dates = [date for date in prev_dates if not pd.isna(date)]
            prev_closes = [float(close) for close in prev_closes if close and close != '']

            high1 = float(row['High 1'])
            high2 = float(row['High 2'])
            current_close = float(row['Current Close Price'])
            B = max(pd.to_datetime(row['Date 1']), pd.to_datetime(row['Date 2'], errors='coerce'))
            A = max(high1, high2)

            condition1 = A < current_close
            if B in prev_dates:
                index = prev_dates.index(B)
                prev_closes_in_range = prev_closes[:index + 1]
                condition2 = all(A >= close for close in prev_closes_in_range)
            else:
                condition2 = False

            if condition1 and condition2:
                results.append(row)

        except Exception:
            continue
    return pd.DataFrame(results)

# -------------------------------
# Streamlit UI (Manual Input)
# -------------------------------
st.title("📈 NSE Stock High Difference Finder (Manual Input Version)")

stock_input = st.text_input("Enter stock symbol(s) separated by commas", "RELIANCE.NS, TCS.NS")

if stock_input:
    nse_symbols = [s.strip() for s in stock_input.split(",") if s.strip()]

    if nse_symbols:
        min_price = st.number_input("Min Closing Price", value=0.0)
        max_price = st.number_input("Max Closing Price", value=8000.0)
        price_range = (min_price, max_price)

        batch_size = st.selectbox("Select Batch Size", [1, 5, 10, 20, 50], index=0)

        selected_date = st.date_input("Select Current Date", datetime.date.today())

        if st.button("Run Analysis"):
            log_placeholder = st.empty()
            st.info(f"Fetching data up to {selected_date}, please wait...")

            raw_results = analyze_stocks_in_batches(
                nse_symbols,
                price_range=price_range,
                batch_size=batch_size,
                log_placeholder=log_placeholder,
                custom_date=selected_date
            )

            if raw_results:
                df = pd.DataFrame(raw_results)
                filtered_df = process_data(df)
                if not filtered_df.empty:
                    st.success("✅ Filtered Results:")
                    st.dataframe(filtered_df)
                else:
                    st.warning("No data meets the conditions.")
            else:
                st.warning("No stocks met the criteria.")
else:
    st.write("Please enter at least one stock symbol.")
