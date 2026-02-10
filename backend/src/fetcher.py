import os
import twstock
import yfinance as yf
import pandas as pd
import pickle
import time  # <--- 新增 time 模組
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
        分批下載並處理快取 (避免 Rate Limit)
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
        print(f"開始下載 {len(tickers)} 檔股票數據 (分批執行中)...")
        
        # === 設定分批參數 ===
        BATCH_SIZE = 50      # 每批 50 檔 (降低被 Ban 機率)
        DELAY_SECONDS = 2    # 每批間隔 2 秒
        MAX_RETRIES = 3      # 失敗重試次數
        
        all_dfs = []
        
        # 將 tickers 切割成多個 chunk
        chunks = [tickers[i:i + BATCH_SIZE] for i in range(0, len(tickers), BATCH_SIZE)]
        
        for i, chunk in enumerate(chunks):
            print(f"下載進度: 第 {i+1}/{len(chunks)} 批 ({len(chunk)} 檔)...")
            
            success = False
            for attempt in range(MAX_RETRIES):
                try:
                    # 下載該批次
                    data = yf.download(
                        chunk, 
                        period="2y", 
                        threads=True, 
                        group_by='ticker',
                        auto_adjust=False 
                    )
                    
                    if not data.empty:
                        all_dfs.append(data)
                    success = True
                    break # 成功則跳出重試迴圈
                    
                except Exception as e:
                    print(f"⚠️ 第 {i+1} 批下載失敗 (嘗試 {attempt+1}/{MAX_RETRIES}): {e}")
                    time.sleep(DELAY_SECONDS * (attempt + 1)) # 失敗時睡久一點
            
            if not success:
                print(f"❌ 第 {i+1} 批完全失敗，跳過。")

            # 批次間的間隔 (重要！)
            time.sleep(DELAY_SECONDS)
        
        if not all_dfs:
            print("❌ 所有批次下載皆失敗。")
            return None

        # 3. 合併數據與儲存
        print("下載完成，正在合併數據...")
        try:
            # axis=1 用於合併 columns (不同股票)
            final_data = pd.concat(all_dfs, axis=1)
            
            print("正在寫入快取...")
            with open(self.cache_path, "wb") as f:
                pickle.dump(final_data, f)
                
            return final_data
            
        except Exception as e:
            print(f"數據合併失敗: {e}")
            return None