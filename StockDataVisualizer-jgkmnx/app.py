from flask import Flask, render_template, request
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime


app = Flask(__name__)
API_KEY = '6P95RTQHO9NS644U'

def load_stock_symbols():
    df = pd.read_csv("stocks.csv")
    return sorted(df['Symbol'].dropna().unique())

def fetch_stock_data(symbol, function, interval=None):
    url = 'https://www.alphavantage.co/query'
    params = {
        'function': function,
        'symbol': symbol,
        'apikey': API_KEY,
        'datatype': 'json'
    }

    if interval:
        params['interval'] = interval
        params['outputsize'] = 'compact'
    else:
        params['outputsize'] = 'full'

    response = requests.get(url, params=params)
    data = response.json()

    lookup = {
        "TIME_SERIES_INTRADAY": f"Time Series ({interval})",
        "TIME_SERIES_DAILY": "Time Series (Daily)",
        "TIME_SERIES_WEEKLY": "Weekly Time Series",
        "TIME_SERIES_MONTHLY": "Monthly Time Series"
    }

    return data.get(lookup.get(function), {})



def plot_chart(data, symbol, chart_type):
    df = pd.DataFrame.from_dict(data, orient='index')
    df.index = pd.to_datetime(df.index)
    df = df.rename(columns={
        "1. open": "Open",
        "2. high": "High",
        "3. low": "Low",
        "4. close": "Close",
        "5. volume": "Volume"
    })

    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna()

    if chart_type == "Candlestick Chart":
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close']
        )])
    elif chart_type == "Line Chart":
        fig = go.Figure([go.Scatter(x=df.index, y=df["Close"], mode='lines')])
    elif chart_type == "Bar Chart":
        fig = go.Figure([go.Bar(x=df.index, y=df["Close"])])

    fig.update_layout(
        title=f"{symbol} - {chart_type}",
        xaxis_title="Date",
        yaxis_title="Price",
        template="plotly_dark"
    )

    return fig.to_html(full_html=False)



@app.route('/', methods=['GET', 'POST'])
def index():
    symbols = load_stock_symbols()
    chart_html = None
    errors = []

    if request.method == 'POST':
        symbol = request.form.get('symbol')
        chart_type = request.form.get('chart_type')
        function = request.form.get('time_series')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')


        if symbol not in symbols:
            errors.append("Invalid stock symbol selected.")

        if chart_type not in ["Line Chart", "Candlestick Chart", "Bar Chart"]:
            errors.append("Invalid chart type selected.")

        if function not in [
            "TIME_SERIES_DAILY", 
            "TIME_SERIES_WEEKLY", 
            "TIME_SERIES_MONTHLY", 
            "TIME_SERIES_INTRADAY"
        ]:
            errors.append("Invalid time series selected.")

        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            if end_dt < start_dt:
                errors.append("End date must be after start date.")

        except Exception:
            errors.append("Invalid date format.")



        if not errors:
            interval = '5min' if function == 'TIME_SERIES_INTRADAY' else None
            stock_data = fetch_stock_data(symbol, function, interval)

            if stock_data:
                filtered_data = {
                    date: values for date, values in stock_data.items()
                    if start_date <= date <= end_date
                }

                if filtered_data:
                    chart_html = plot_chart(filtered_data, symbol, chart_type)
                else:
                    errors.append("No data available for the selected date range.")

            else:
                errors.append("Failed to fetch stock data. Try a different symbol or time series.")

    return render_template('index.html', symbols=symbols, chart_html=chart_html, errors=errors)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")

