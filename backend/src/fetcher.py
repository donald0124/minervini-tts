import os
import twstock
import yfinance as yf
import pandas as pd
import pickle
from datetime import datetime
from . import config

class StockFetcher:
    def __init__(self):
        self.cache_path = os.path.join(config.CACHE_DIR, f"market_data_{datetime.now().strftime('%Y-%m-%d')}.pkl")

    def get_universe(self):
        """
        取得台股上市櫃普通股清單 (FR-01)
        回傳: Dictionary { '2330.TW': '台積電', ... }
        """
        print("正在獲取股票代碼與名稱清單...")
        # twstock.codes 是一個字典，包含所有上市櫃股票資訊
        # 我們只取 "股票" 類別，並排除 ETF, DR 等
        tickers_map = {}
        
        for code, info in twstock.codes.items():
            if info.type == "股票":
                # 簡單過濾：排除 00開頭(ETF/債券等), 91開頭(DR)
                if code.startswith("00") or code.startswith("91"):
                    continue
                
                # 區分上市 (.TW) 與上櫃 (.TWO)
                full_code = ""
                if info.market == "上市":
                    full_code = f"{code}.TW"
                elif info.market == "上櫃":
                    full_code = f"{code}.TWO"
                
                if full_code:
                    tickers_map[full_code] = info.name
        
        print(f"共取得 {len(tickers_map)} 檔普通股代碼。")
        return tickers_map

    def fetch_batch(self, tickers):
        """
        批量下載並處理快取 (FR-02, NFR-01)
        tickers: List of strings
        """
        # 1. 檢查快取
        if os.path.exists(self.cache_path):
            print(f"發現今日快取，正在載入：{self.cache_path}")
            try:
                with open(self.cache_path, "rb") as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"快取讀取失敗，將重新下載: {e}")

        # 2. 無快取，執行下載
        print(f"開始下載 {len(tickers)} 檔股票數據 (這可能需要幾分鐘)...")
        # yfinance download 會回傳 MultiIndex DataFrame
        data = yf.download(
            tickers, 
            period="2y", # 確保有足夠數據計算 52週高低
            threads=True, 
            group_by='ticker',
            auto_adjust=False 
        )
        
        # 3. 儲存快取
        print("下載完成，正在寫入快取...")
        with open(self.cache_path, "wb") as f:
            pickle.dump(data, f)
            
        return data