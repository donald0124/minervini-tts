import pandas as pd
import numpy as np
from . import config

class DataProcessor:
    def process_data(self, raw_data, tickers):
        """
        執行 ETL 流程：清洗 -> 計算個股指標 -> 計算 RS 排名
        回傳: 一個 Dictionary，Key 是 ticker, Value 是處理好的 DataFrame (單檔)
        """
        processed_stocks = {}
        valid_rocs = [] # 用來存 1 年漲幅以計算 RS

        print("開始進行技術指標運算與流動性過濾...")

        for ticker in tickers:
            try:
                # 處理 yfinance 的 MultiIndex 結構
                # 如果只有一檔股票，yfinance 不會回傳 MultiIndex，需做相容性處理
                if isinstance(raw_data.columns, pd.MultiIndex):
                    df = raw_data[ticker].copy()
                else:
                    df = raw_data.copy()

                # FR-02: IPO 規則 (資料不足 250 天剔除)
                if len(df) < config.IPO_MIN_DAYS:
                    continue

                # 使用 'Adj Close' 進行計算，若無則用 'Close'
                target_col = 'Adj Close' if 'Adj Close' in df.columns else 'Close'
                
                # === 流動性過濾 (FR-06) ===
                # 計算 20日均量
                df['Vol_SMA_20'] = df['Volume'].rolling(window=20).mean()
                current_vol_avg = df['Vol_SMA_20'].iloc[-1]
                
                # 若流動性不足，直接跳過不加入後續清單 (或標記為 Fail，此處選擇保留以便 Validator 標記原因)
                # 為了加速 RS 運算，我們這裡先只保留流動性合格的進入 RS 池
                # 但為了 Report 能顯示 "Liquidity Fail"，我們還是全算，但在 Validator 擋
                
                # === 技術指標運算 (Pass 1) ===
                # 均線
                df['SMA_50'] = df[target_col].rolling(window=50).mean()
                df['SMA_150'] = df[target_col].rolling(window=150).mean()
                df['SMA_200'] = df[target_col].rolling(window=200).mean()
                
                # 200MA 斜率 (比較今日與 22 天前)
                df['SMA_200_Prev'] = df['SMA_200'].shift(config.MA_SLOPE_LOOKBACK)
                
                # 52週高低
                df['High_52W'] = df[target_col].rolling(window=252).max()
                df['Low_52W'] = df[target_col].rolling(window=252).min()
                
                # 1年 ROC (用於 RS 計算)
                # 取 250 天前的價格來算漲幅
                start_price = df[target_col].shift(250)
                df['ROC_1Y'] = (df[target_col] - start_price) / start_price
                
                # 存入結果
                current_roc = df['ROC_1Y'].iloc[-1]
                if not pd.isna(current_roc):
                    valid_rocs.append(current_roc)
                
                processed_stocks[ticker] = df

            except KeyError:
                continue
            except Exception as e:
                # print(f"Error processing {ticker}: {e}")
                continue

        # === RS 排名運算 (Pass 2) (FR-03) ===
        print("正在計算全市場 RS 評分...")
        # 將所有 ROC 轉為 Series
        roc_series = pd.Series(valid_rocs)
        
        # 計算百分位數 (0-1) 並轉為 0-99 分
        # 使用 rank(pct=True)
        
        for ticker, df in processed_stocks.items():
            current_roc = df['ROC_1Y'].iloc[-1]
            if pd.isna(current_roc):
                df['RS_Rating'] = 0
            else:
                # 這裡簡單實作：算出該 ROC 在所有 ROC 中的 PR 值
                # 實務上更快的做法是先算出 rank map，但這裡迴圈跑也還行
                percentile = (roc_series < current_roc).mean()
                df['RS_Rating'] = int(percentile * 99)
            
            processed_stocks[ticker] = df # 更新 DataFrame

        return processed_stocks