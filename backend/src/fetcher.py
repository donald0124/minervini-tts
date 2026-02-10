import os
import twstock
import yfinance as yf
import pandas as pd
import pickle
import time
import random
import requests # <--- 必須引入
from datetime import datetime
from . import config

class StockFetcher:
    def __init__(self):
        self.cache_path = os.path.join(config.CACHE_DIR, f"market_data_{datetime.now().strftime('%Y-%m-%d')}.pkl")
        
        # === 建立偽裝瀏覽器的 Session ===
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
        })

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
        分批下載並處理快取 (偽裝瀏覽器 + 強制冷卻版)
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
        print(f"開始下載 {len(tickers)} 檔股票數據 (Zeabur 匿蹤模式)...")
        
        # === 參數設定 ===
        BATCH_SIZE = 8       # 極小批次 (8檔)
        NORMAL_DELAY_MIN = 8 # 正常等待下限 (秒)
        NORMAL_DELAY_MAX = 15 # 正常等待上限 (秒)
        ERROR_COOLDOWN = 180 # 遇到封鎖時，強制冷卻 3 分鐘 (秒)
        MAX_RETRIES = 3      
        
        all_dfs = []
        chunks = [tickers[i:i + BATCH_SIZE] for i in range(0, len(tickers), BATCH_SIZE)]
        total_batches = len(chunks)
        
        for i, chunk in enumerate(chunks):
            current_batch = i + 1
            print(f"[{current_batch}/{total_batches}] 正在下載 {len(chunk)} 檔...")
            
            success = False
            for attempt in range(MAX_RETRIES):
                try:
                    # 使用 session 參數傳入偽裝的 headers
                    data = yf.download(
                        chunk, 
                        period="2y", 
                        threads=False, # 關閉多執行緒，減少並發請求被抓的機率
                        group_by='ticker',
                        auto_adjust=False,
                        session=self.session # <--- 關鍵：使用偽裝 Session
                    )
                    
                    if not data.empty:
                        all_dfs.append(data)
                        success = True
                        
                        # 隨機延遲
                        sleep_time = random.uniform(NORMAL_DELAY_MIN, NORMAL_DELAY_MAX)
                        print(f"   ✅ 成功。休息 {sleep_time:.1f} 秒...")
                        time.sleep(sleep_time)
                        break 
                    else:
                        print(f"   ⚠️ 無數據 (Attempt {attempt+1})。")
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(10)
                        
                except Exception as e:
                    error_msg = str(e)
                    print(f"   ❌ 失敗: {error_msg}")
                    
                    # 如果是 Rate Limit 錯誤，啟動長時冷卻
                    if "Too Many Requests" in error_msg or "Rate limited" in error_msg:
                        print(f"   ⛔️ 被 Yahoo 封鎖偵測！強制冷卻 {ERROR_COOLDOWN} 秒...")
                        time.sleep(ERROR_COOLDOWN)
                    else:
                        # 普通錯誤，休息一下就好
                        time.sleep(30)
            
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