import os
import twstock
import yfinance as yf
import pandas as pd
import pickle
import time
import random
from datetime import datetime, timedelta
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
        分批下載 (包含資料長度檢查，防止 Yahoo 給截斷的數據)
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
        print(f"開始下載 {len(tickers)} 檔股票數據 (完整模式)...")
        
        # === 參數設定 ===
        BATCH_SIZE = 300       # 保持小批次
        NORMAL_DELAY_MIN = 5  # 正常等待
        NORMAL_DELAY_MAX = 12
        ERROR_COOLDOWN = 60   # 遇到長度不足或封鎖，休息 1 分鐘
        MAX_RETRIES = 3
        MIN_HISTORY_LEN = 250 # 關鍵：至少要有 250 天的資料才算成功
        
        # 設定起始日期 (強制抓 3 年)
        start_date = (datetime.now() - timedelta(days=1000)).strftime('%Y-%m-%d')
        
        all_dfs = []
        chunks = [tickers[i:i + BATCH_SIZE] for i in range(0, len(tickers), BATCH_SIZE)]
        total_batches = len(chunks)
        
        for i, chunk in enumerate(chunks):
            current_batch = i + 1
            print(f"[{current_batch}/{total_batches}] 正在下載 {len(chunk)} 檔...", end="", flush=True)
            
            success = False
            for attempt in range(MAX_RETRIES):
                try:
                    data = yf.download(
                        chunk, 
                        start=start_date, # 強制指定起始日
                        threads=False,    # 關閉多線程以穩定數據
                        group_by='ticker',
                        auto_adjust=False,
                        progress=False    # 關閉 yfinance 內建進度條以免洗版
                    )
                    
                    if not data.empty:
                        # === 關鍵檢查：資料長度夠嗎？ ===
                        # 取出這批資料的列數 (天數)
                        data_len = len(data)
                        
                        if data_len < MIN_HISTORY_LEN:
                            # 資料太短！判定為 Yahoo 截斷數據 (Soft Ban)
                            print(f"\n   ⚠️ 警告：資料長度不足 ({data_len} 天 < {MIN_HISTORY_LEN} 天)。判定為流量限制截斷。")
                            raise ValueError("Data truncated by Yahoo (Soft Ban)")
                        
                        # 成功
                        all_dfs.append(data)
                        success = True
                        
                        # 隨機延遲
                        sleep_time = random.uniform(NORMAL_DELAY_MIN, NORMAL_DELAY_MAX)
                        print(f" ✅ 成功 ({data_len} 天)。休息 {sleep_time:.1f}s...")
                        time.sleep(sleep_time)
                        break 
                    else:
                        print(f"\n   ⚠️ 無數據 (Attempt {attempt+1})。")
                        time.sleep(10)
                        
                except Exception as e:
                    error_msg = str(e)
                    # 判斷是否需要長時冷卻
                    if "truncated" in error_msg or "Too Many Requests" in error_msg or "429" in error_msg:
                        print(f"\n   ⛔️ 被 Yahoo 限制流量 (Attempt {attempt+1})！冷卻 {ERROR_COOLDOWN} 秒...")
                        time.sleep(ERROR_COOLDOWN)
                    else:
                        print(f"\n   ❌ 失敗: {error_msg}。重試中...")
                        time.sleep(15)
            
            if not success:
                print(f"\n   ❌ 第 {current_batch} 批完全失敗 (已達重試上限)，跳過。")

        if not all_dfs:
            print("❌ 所有批次下載皆失敗，無法產生數據。")
            return None

        # 3. 合併數據與儲存
        print("\n下載完成，正在合併數據...")
        try:
            final_data = pd.concat(all_dfs, axis=1)
            
            print("正在寫入快取...")
            with open(self.cache_path, "wb") as f:
                pickle.dump(final_data, f)
                
            return final_data
            
        except Exception as e:
            print(f"數據合併失敗: {e}")
            return None