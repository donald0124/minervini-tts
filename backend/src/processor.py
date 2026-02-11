import pandas as pd
import numpy as np
from . import config

class DataProcessor:
    def process_data(self, raw_data, tickers):
        """
        執行 ETL 流程：清洗 -> 計算個股指標 -> 計算 RS 排名
        """
        processed_stocks = {}
        valid_rocs = [] 

        print(f"開始處理 {len(tickers)} 檔股票數據...")

        # 檢查 raw_data 是否為空
        if raw_data is None or raw_data.empty:
            print("❌ 錯誤：傳入的 raw_data 為空！")
            return {}

        # 判斷是否為多層索引 (MultiIndex)
        is_multi_index = isinstance(raw_data.columns, pd.MultiIndex)

        for ticker in tickers:
            try:
                # === 1. 資料提取與欄位標準化 ===
                df = None
                
                if is_multi_index:
                    # 檢查該 ticker 是否在資料中
                    if ticker not in raw_data.columns.levels[0]:
                        continue
                    df = raw_data[ticker].copy()
                else:
                    # 單一股票的情況 (很少見，但以防萬一)
                    if len(tickers) == 1:
                        df = raw_data.copy()
                    else:
                        continue

                # 移除全空行 (沒交易的日子)
                df.dropna(how='all', inplace=True)

                # [關鍵修正] 強制扁平化欄位：如果還殘留多層索引，強制取第一層
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                # === 2. 資料品質檢查 ===
                # FR-02: IPO 規則 (資料不足 250 天剔除)
                if len(df) < config.IPO_MIN_DAYS:
                    # [DEBUG] 如果是台積電卻被剔除，要印出來
                    if ticker == "2330.TW":
                        print(f"⚠️ [DEBUG] 2330.TW 資料長度不足 ({len(df)} < {config.IPO_MIN_DAYS})，將被略過。")
                    continue

                # 決定使用哪個價格欄位
                if 'Adj Close' in df.columns:
                    target_col = 'Adj Close'
                elif 'Close' in df.columns:
                    target_col = 'Close'
                else:
                    # 連 Close 都沒有，直接跳過
                    continue

                # === [DEBUG] 針對特定股票印出診斷訊息 (確保運算正常) ===
                if ticker == "2330.TW": # 您可以改成任何一檔您確定應該要有資料的股票
                    print(f"\n🔍 [DEBUG] 正在運算 {ticker} ...")
                    print(f"   - 資料長度: {len(df)} 天")
                    print(f"   - 最新收盤日: {df.index[-1].date()}")
                    print(f"   - 最新價格: {df[target_col].iloc[-1]}")

                # === 3. 技術指標運算 ===
                
                # 流動性：20日均量
                df['Vol_SMA_20'] = df['Volume'].rolling(window=20).mean()
                
                # 移動平均線 (SMA)
                df['SMA_50'] = df[target_col].rolling(window=50).mean()
                df['SMA_150'] = df[target_col].rolling(window=150).mean()
                df['SMA_200'] = df[target_col].rolling(window=200).mean()
                
                # 200MA 斜率 (比較今日與 20 天前，這裡 config 預設通常是 20 或 22)
                # 使用 shift 來比較
                lookback = config.MA_SLOPE_LOOKBACK if hasattr(config, 'MA_SLOPE_LOOKBACK') else 20
                df['SMA_200_Prev'] = df['SMA_200'].shift(lookback)
                
                # 52週高低 (252天)
                df['High_52W'] = df[target_col].rolling(window=252).max()
                df['Low_52W'] = df[target_col].rolling(window=252).min()


                # === 原本的寫法 (已註解掉) ===
                # start_price = df[target_col].shift(250)
                # df['ROC_1Y'] = (df[target_col] - start_price) / start_price
                
                # === 新增：IBD 風格的加權 RS 算法 ===
                # 定義四個時間窗口 (以交易日計算，一季約 63 天)
                roc_3m = df[target_col].pct_change(periods=63)
                roc_6m = df[target_col].pct_change(periods=126)
                roc_9m = df[target_col].pct_change(periods=189)
                roc_12m = df[target_col].pct_change(periods=252)

                # 加權計算 (近期權重 40%，其餘各 20%)
                # 注意：fillna(0) 是為了避免新上市股票前面是 NaN 導致結果為 NaN
                # 但更嚴謹的做法是若資料不足 252 天，權重應重新分配 (這裡先簡化處理)
                df['Weighted_ROC'] = (0.4 * roc_3m) + (0.2 * roc_6m) + (0.2 * roc_9m) + (0.2 * roc_12m)
                
                # 存入結果 (改用 Weighted_ROC)
                current_roc = df['Weighted_ROC'].iloc[-1]
                if not pd.isna(current_roc):
                    valid_rocs.append(current_roc)


                # === [DEBUG] 檢查算出來的結果 ===
                if ticker == "2330.TW":
                    print(f"   - SMA_50: {df['SMA_50'].iloc[-1]:.2f}")
                    print(f"   - SMA_150: {df['SMA_150'].iloc[-1]}") # 如果是 NaN 代表沒算出
                    print(f"   - SMA_200: {df['SMA_200'].iloc[-1]}")
                    if pd.isna(df['SMA_200'].iloc[-1]):
                        print("   ❌ [嚴重] SMA_200 計算結果為 NaN！(可能歷史資料長度剛好卡邊緣)")
                
                # 收集有效的 ROC 用於後續排名
                current_roc = df['ROC_1Y'].iloc[-1]
                if not pd.isna(current_roc):
                    valid_rocs.append(current_roc)
                
                processed_stocks[ticker] = df

            except Exception as e:
                print(f"⚠️ 處理 {ticker} 時發生錯誤: {e}")
                continue

        # === 4. RS 排名運算 (Pass 2) ===
        print(f"正在計算 RS 評分 (有效樣本數: {len(valid_rocs)})...")
        
        if not valid_rocs:
            print("❌ 警告：沒有任何有效的 ROC 數據，RS 評分將全為 0。")
            return processed_stocks

        # 將 list 轉為 Series 以便大量運算
        roc_series = pd.Series(valid_rocs).sort_values()
        
        for ticker, df in processed_stocks.items():
            try:
                current_roc = df['Weighted_ROC'].iloc[-1]
                
                if pd.isna(current_roc):
                    df['RS_Rating'] = 0
                else:
                    # 使用 percentileofscore 或是簡單的 rank 邏輯
                    # 這裡使用簡單邏輯：贏過多少百分比的人
                    # searchsorted 回傳的是「如果插入這個值，會排在第幾個索引」
                    # 索引位置 / 總數 = 百分比
                    rank_idx = roc_series.searchsorted(current_roc, side='right')
                    percentile = (rank_idx / len(roc_series)) * 99
                    df['RS_Rating'] = int(percentile)
                
                processed_stocks[ticker] = df
                
            except Exception:
                df['RS_Rating'] = 0
                processed_stocks[ticker] = df

        return processed_stocks