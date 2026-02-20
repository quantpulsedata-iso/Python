import yfinance as yf
import pandas as pd
import numpy as np
import time
import os
from datetime import datetime
from colorama import init, Fore, Back, Style

# Windows terminalinde renkleri aktif et
init(autoreset=True)

class WhaleScanner:
    def __init__(self, asset_list):
        self.asset_list = asset_list
        self.results = []

    def calculate_rsi(self, data, window=14):
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def run_scan(self):
        # Başlık Kısmı
        print(Fore.CYAN + Style.BRIGHT + "\n" + "="*75)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] QUANT PULSE DATA: DEEP MARKET ANALYSIS")
        print("="*75 + "\n")
        
        for ticker in self.asset_list:
            try:
                # Veri indirme
                df = yf.download(ticker, period="60d", interval="1d", progress=False)
                
                if df.empty or len(df) < 30: 
                    continue

                # Veri temizleme (Squeeze)
                close_series = df['Close'].squeeze()
                volume_series = df['Volume'].squeeze()

                # Teknik Hesaplamalar
                rsi_values = self.calculate_rsi(close_series)
                last_close = float(close_series.iloc[-1])
                last_rsi = float(rsi_values.iloc[-1])
                avg_vol = float(volume_series.mean())
                last_vol = float(volume_series.iloc[-1])

                # Renkli Durum ve Analist Notu Belirleme
                if last_rsi < 30:
                    status = f"{Fore.RED}[OVERSOLD - HIGH RISK]"
                    note = "Panic Selling detected. No Whale entry yet."
                elif 30 <= last_rsi < 55 and last_vol > avg_vol * 1.1:
                    status = f"{Fore.GREEN}[MATCH FOUND - WHALE IN]"
                    note = "Strong Momentum & Volume. Breakout likely."
                    self.results.append({'Ticker': ticker, 'Price': last_close, 'RSI': last_rsi})
                elif last_rsi > 70:
                    status = f"{Fore.YELLOW}[OVERBOUGHT - COOLING]"
                    note = "Price peaked. Waiting for correction."
                else:
                    status = f"{Fore.WHITE}[NEUTRAL]"
                    note = "Scanning for volume spikes..."

                # Satırı Yazdır
                ticker_display = f"{Style.BRIGHT}{ticker:10}"
                print(f"{ticker_display} | {status:35} {Style.RESET_ALL} | RSI: {last_rsi:4.1f} | {note}")
                
                time.sleep(0.8) # Akış efekti için

            except Exception as e:
                print(f"{Fore.RED}[ERROR] {ticker}: {e}")

        self.save_report()

    def save_report(self):
        target_dir = r"C:\temp"
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        
        file_path = os.path.join(target_dir, "Whale_Scan_Report.csv")

        if self.results:
            try:
                report_df = pd.DataFrame(self.results)
                report_df.to_csv(file_path, index=False)
                print(f"\n{Fore.GREEN}{Style.BRIGHT}[SUCCESS]{Style.RESET_ALL} Report saved to: {file_path}")
            except PermissionError:
                print(f"\n{Fore.RED}[ERROR] Close the CSV file before running!")
        else:
            print(f"\n{Fore.YELLOW}[INFO] Scan complete. No Whale activity detected.")

# İzleme Listesi
watch_list = ["BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "NVDA", "TSLA", "AAPL", "AMD", "COIN", "MSFT", "GOOGL", "META"]

if __name__ == "__main__":
    try:
        scanner = WhaleScanner(watch_list)
        scanner.run_scan()
        
        print(f"\n{Fore.CYAN}" + "="*75)
        print(f"{Style.BRIGHT}PROCESS COMPLETE. DATA SECURED.")
        print("Press ENTER to close the terminal...")
        print("="*75)
        input() 
    except Exception as e:
        print(f"\n{Fore.RED}CRITICAL ERROR: {e}")
        input("Press ENTER to exit...")
