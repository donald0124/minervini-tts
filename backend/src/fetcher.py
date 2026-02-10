import os
import twstock
import yfinance as yf
import pandas as pd
import pickle
import time
import random  # 引入 random 以產生隨機延遲
from datetime import datetime
from . import config

class StockFetcher:
    def __init__(self):
        self.cache_path = os.path.join(config.CACHE_DIR, f"market_data_{datetime.now().strftime('%Y-%m-%d')}.pkl")

    def get_universe(self):
        """
        取得台股上市櫃普通股清單
        """
        print("正在獲取股票代碼與名稱清單...")
        tickers_map = {}
        
        for code, info in twstock.codes.items():
            if info.type == "股票":
                if code.startswith("00") or code.startswith("91"):
                    continue
                
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
        分批下載並處理快取 (針對雲端環境優化版)
        """
        # 1. 檢查快取
        if os.path.exists(self.cache_path):
            print(f"發現今日快取，正在載入：{self.cache_path}")
            try:
                with open(self.cache_path, "rb") as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"快取讀取失敗，將重新下載: {e}")

        # 2. 無快取，執行分批下載
        print(f"開始下載 {len(tickers)} 檔股票數據 (雲端慢速模式)...")
        
        # === 雲端環境極限參數 ===
        BATCH_SIZE = 20       # 每批只抓 15 檔 (非常保守)
        MIN_DELAY = 12        # 最小等待 12 秒
        MAX_DELAY = 25        # 最大等待 25 秒
        MAX_RETRIES = 5       # 增加重試次數
        
        all_dfs = []
        chunks = [tickers[i:i + BATCH_SIZE] for i in range(0, len(tickers), BATCH_SIZE)]
        total_batches = len(chunks)
        
        for i, chunk in enumerate(chunks):
            current_batch = i + 1
            print(f"[{current_batch}/{total_batches}] 正在下載 {len(chunk)} 檔...")
            
            success = False
            for attempt in range(MAX_RETRIES):
                try:
                    data = yf.download(
                        chunk, 
                        period="2y", 
                        threads=True, # 保持 True，單一批次內還是可以並行
                        group_by='ticker',
                        auto_adjust=False 
                    )
                    
                    if not data.empty:
                        all_dfs.append(data)
                        success = True
                        
                        # 隨機延遲 (讓行為看起來不像機器人)
                        sleep_time = random.uniform(MIN_DELAY, MAX_DELAY)
                        print(f"   ✅ 成功。休息 {sleep_time:.1f} 秒...")
                        time.sleep(sleep_time)
                        break 
                    else:
                        # 雖然沒有 Exception 但沒資料，可能也是被擋，稍作休息
                        print(f"   ⚠️ 無數據。重試中...")
                        time.sleep(10)
                        
                except Exception as e:
                    wait_time = (attempt + 2) * 10 # 失敗時等待 20, 30, 40... 秒
                    print(f"   ❌ 失敗 ({e})。等待 {wait_time} 秒後重試 ({attempt+1}/{MAX_RETRIES})...")
                    time.sleep(wait_time)
            
            if not success:
                print(f"   ❌ 第 {current_batch} 批完全失敗，跳過。")

        if not all_dfs:
            print("❌ 所有批次下載皆失敗，無法產生數據。")
            return None

        # 3. 合併數據與儲存
        print("下載完成，正在合併數據...")
        try:
            final_data = pd.concat(all_dfs, axis=1)
            
            print("正在寫入快取...")
            with open(self.cache_path, "wb") as f:
                pickle.dump(final_data, f)
                
            return final_data
            
        except Exception as e:
            print(f"數據合併失敗: {e}")
            return None