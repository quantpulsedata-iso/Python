import requests
import pandas as pd
import numpy as np
import time
from colorama import init, Fore, Style
import warnings
warnings.filterwarnings("ignore")
init(autoreset=True)

BASE_URL = "https://data-api.binance.vision"  # Stable public endpoint

def get_binance_symbols():
    """Fetch Binance spot symbols + volume filter"""
    url = f"{BASE_URL}/api/v3/ticker/24hr"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"{Fore.RED}Ticker status: {response.status_code}")
            raise ValueError("Bad response")
        
        data = response.json()
        
        symbols_data = []
        for item in data:
            if item['symbol'].endswith('USDT'):
                try:
                    vol = float(item['quoteVolume'])
                    if vol > 2500000:
                        symbols_data.append((item['symbol'], vol))
                except:
                    pass
        
        symbols_data.sort(key=lambda x: x[1], reverse=True)
        symbols = [s[0] for s in symbols_data]
        
        return symbols[:15]  # Top 15 most active
    except Exception as e:
        print(f"{Fore.RED}Symbols fetch error: {str(e)}")
        return ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']

def get_klines(symbol, interval='1h', limit=100):
    """Fetch Binance kline data"""
    url = f"{BASE_URL}/api/v3/klines"
    params = {'symbol': symbol, 'interval': interval, 'limit': limit}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            print(f"{Fore.RED}{symbol} klines status: {response.status_code}")
            return pd.DataFrame()
        
        data = response.json()
        if not data or not isinstance(data, list):
            return pd.DataFrame()
        
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.dropna(subset=['close'])
        return df
    except Exception as e:
        print(f"{Fore.RED}{symbol} klines error: {str(e)}")
        return pd.DataFrame()

def calculate_bollinger_bands(df):
    """Calculate Bollinger Bands"""
    df = df.copy()
    df['MA20'] = df['close'].rolling(20).mean()
    df['STD20'] = df['close'].rolling(20).std()
    df['Upper'] = df['MA20'] + (df['STD20'] * 2)
    df['Lower'] = df['MA20'] - (df['STD20'] * 2)
    df['BW'] = (df['Upper'] - df['Lower']) / df['MA20'] * 100
    return df

# 🔥 5 PROFESSIONAL MODELS (names & logic unchanged, just English labels)
def model_1_sling(df):
    """1️⃣ SLINGSHOT MODEL"""
    if len(df) < 30: return False, 0
    bw_squeeze = df['BW'].tail(10).mean() < df['BW'].tail(30).mean() * 0.85
    breakout = df['close'].tail(2).mean() > df['Upper'].tail(2).mean()
    pullback = df['close'].iloc[-1] > df['MA20'].iloc[-1] * 0.995
    score = sum([bw_squeeze, breakout, pullback])
    return score >= 2, score * 33

def model_2_rubber_band(df):
    """2️⃣ RUBBER BAND"""
    if len(df) < 30: return False, 0
    lower_out = df['close'].iloc[-1] < df['Lower'].iloc[-1] * 0.98
    support = df['low'].tail(50).min() >= df['close'].iloc[-1] * 0.95
    strong_close = abs(df['close'].iloc[-1] - df['open'].iloc[-1]) > df['close'].tail(5).std()
    score = sum([lower_out, support, strong_close])
    return score >= 2, score * 33

def model_3_ladder(df):
    """3️⃣ LADDER CLIMB"""
    if len(df) < 30: return False, 0
    ma_uptrend = df['MA20'].iloc[-1] > df['MA20'].iloc[-5]
    above_ma = df['close'].iloc[-1] > df['MA20'].iloc[-1]
    bounce_lower = (df['low'].iloc[-2] <= df['Lower'].iloc[-2]) and (df['close'].iloc[-1] > df['MA20'].iloc[-1])
    score = sum([ma_uptrend, above_ma, bounce_lower])
    return score >= 2, score * 33

def model_4_divergence(df):
    """4️⃣ DIVERGENCE (RSI)"""
    if len(df) < 30: return False, 0
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    price_low = df['close'].iloc[-1] < df['Lower'].iloc[-1]
    rsi_divergence = (df['low'].iloc[-10] < df['low'].iloc[-20]) and (rsi.iloc[-10] > rsi.iloc[-20])
    vol_up = df['volume'].iloc[-1] > df['volume'].tail(10).mean()
    
    score = sum([price_low, rsi_divergence, vol_up])
    return score >= 2, score * 33

def model_5_three_green(df):
    """5️⃣ THREE GREEN LIGHTS"""
    if len(df) < 50: return False, 0
    position_ok = df['close'].iloc[-1] > df['MA20'].iloc[-1]
    trend_ok = df['close'].rolling(50).mean().iloc[-1] > df['close'].rolling(200).mean().iloc[-1]
    green_candle = df['close'].iloc[-1] > df['open'].iloc[-1]
    score = sum([position_ok, trend_ok, green_candle])
    return score >= 2, score * 33

def scan_binance_pro():
    print(f"{Fore.MAGENTA}{'='*100}")
    print(f"{Fore.MAGENTA}🔥 BINANCE SPOT BB PRO V5.0 - 500K$+ VOLUME - 5 MODELS 🔥")
    print(f"{Fore.MAGENTA}{'='*100}")
    print(f"{Fore.CYAN}{'TIME':<12} | {'SYMBOL':<12} | {'MODEL':<10} | {'SCORE':<6} | {'PRICE':<12} | {'STATUS'}")
    print("-" * 100)
    
    while True:
        try:
            symbols = get_binance_symbols()
            print(f"{Fore.CYAN}Scanning {len(symbols)} symbols (500K$+ volume)...")
            
            signals_found = 0
            for symbol in symbols:
                try:
                    df = get_klines(symbol)
                    if df.empty or len(df) < 50: 
                        continue
                    
                    df = calculate_bollinger_bands(df)
                    
                    models = [
                        ("SLING", model_1_sling),
                        ("RUBBER", model_2_rubber_band),
                        ("LADDER", model_3_ladder),
                        ("DIVERG", model_4_divergence),
                        ("3GREEN", model_5_three_green)
                    ]
                    
                    for model_name, model_func in models:
                        is_signal, score = model_func(df)
                        if is_signal:
                            current_time = time.strftime('%H:%M:%S')
                            current_price = df['close'].iloc[-1]
                            
                            status = "🚀 BUY SIGNAL"
                            print(f"{Fore.GREEN}{current_time:<12} | "
                                  f"{symbol:<12} | "
                                  f"{model_name:<10} | "
                                  f"{score:<6} | "
                                  f"${current_price:.4f} | "
                                  f"{status}")
                            signals_found += 1
                            break  # Stop after first signal per symbol
                
                except Exception as inner_e:
                    print(f"{Fore.RED}{symbol} processing error: {str(inner_e)}")
                    continue
            
            if signals_found == 0:
                print(f"{Fore.YELLOW}{time.strftime('%H:%M:%S'):<12} | {'SCANNING':<12} | {'WAITING FOR SIGNAL...':<44}")
            
            print(f"{Fore.BLUE}{'─'*100}")
            time.sleep(30)
        
        except KeyboardInterrupt:
            print(f"\n{Fore.RED}Binance scanner stopped!")
            break
        except Exception as e:
            print(f"{Fore.RED}Loop error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    scan_binance_pro()
