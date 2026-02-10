import os
import twstock
import yfinance as yf
import pandas as pd
import pickle
import time
import random
from datetime import datetime
from . import config

class StockFetcher:
    def __init__(self):
        self.cache_path = os.path.join(config.CACHE_DIR, f"market_data_{datetime.now().strftime('%Y-%m-%d')}.pkl")
        # 移除 requests.Session 的建立

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
        分批下載並處理快取 (yfinance 原生抗封鎖版)
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
        print(f"開始下載 {len(tickers)} 檔股票數據 (Zeabur 慢速模式)...")
        
        # === 參數設定 ===
        # 雖然不能用自訂 Session，但我們仍需保持極慢速來保護雲端 IP
        BATCH_SIZE = 2000      # 10 檔一批
        NORMAL_DELAY_MIN = 10
        NORMAL_DELAY_MAX = 20
        ERROR_COOLDOWN = 180 # 遇到封鎖冷卻 3 分鐘
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
                    # 移除 session 參數，讓 yfinance 自己處理
                    data = yf.download(
                        chunk, 
                        period="2y", 
                        threads=False, # 建議關閉多執行緒以降低併發
                        group_by='ticker',
                        auto_adjust=False
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
                    
                    if "Too Many Requests" in error_msg or "Rate limited" in error_msg or "429" in error_msg:
                        print(f"   ⛔️ 被 Yahoo 封鎖偵測！強制冷卻 {ERROR_COOLDOWN} 秒...")
                        time.sleep(ERROR_COOLDOWN)
                    else:
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