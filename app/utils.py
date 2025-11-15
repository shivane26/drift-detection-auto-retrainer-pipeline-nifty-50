import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ta

TICKER = "^NSEI"

def fetch_nifty(years=5):
    end = datetime.today().date()
    start = end - timedelta(days=365*years)
    df = yf.download(TICKER, start=start, end=end, progress=False)
    
    # Handle multi-index columns from yfinance
    if isinstance(df.columns, pd.MultiIndex):
        # Flatten columns: keep first level (OHLCV names), drop ticker names
        df.columns = [col[0] for col in df.columns]
    
    df = df[['Open','High','Low','Close','Volume']].reset_index()
    return df

def add_features(df):
    df = df.copy()
    
    # Ensure columns are flat (not multi-index tuples) - CRITICAL FIX
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
    elif any(isinstance(col, tuple) for col in df.columns):
        # Reconstruct dataframe with string column names
        new_columns = {}
        for col in df.columns:
            if isinstance(col, tuple):
                new_columns[col] = col[0]
            else:
                new_columns[col] = col
        df = df.rename(columns=new_columns)
    
    # Explicitly recreate the dataframe to ensure clean columns
    df = pd.DataFrame(df)
    
    df['return'] = df['Close'].pct_change()

    # Lags
    for lag in [1,2,3,5,7]:
        df[f'ret_lag_{lag}'] = df['return'].shift(lag)

    df['sma_5'] = df['Close'].rolling(5).mean()
    df['sma_10'] = df['Close'].rolling(10).mean()

    # Use pandas EMA instead of ta library to avoid 2D array issue
    df['ema_12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['ema_26'] = df['Close'].ewm(span=26, adjust=False).mean()

    macd = df['ema_12'] - df['ema_26']
    df['macd'] = macd
    df['macd_signal'] = macd.ewm(span=9).mean()

    # RSI calculation (alternative to ta library)
    df['rsi_14'] = calculate_rsi(df['Close'], window=14)

    # Bollinger Bands (alternative to ta library)
    bb_result = calculate_bollinger_bands(df['Close'], window=20, num_std=2)
    df['bb_width'] = bb_result

    df['vol_10'] = df['return'].rolling(10).std()

    df = df.dropna().reset_index(drop=True)
    return df

def calculate_rsi(prices, window=14):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_bollinger_bands(prices, window=20, num_std=2):
    """Calculate Bollinger Bands width"""
    sma = prices.rolling(window).mean()
    std = prices.rolling(window).std()
    upper_band = sma + (std * num_std)
    lower_band = sma - (std * num_std)
    bb_width = (upper_band - lower_band) / prices
    return bb_width

def create_labels(df, horizon=1):
    fut_ret = df['Close'].shift(-horizon) / df['Close'] - 1
    y = (fut_ret > 0).astype(int)
    return y[:-horizon]
