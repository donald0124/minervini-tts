from . import config
import pandas as pd
import json
import csv
import os
import numpy as np # 確保引入 numpy 以處理類型判斷

class MinerviniValidator:
    def validate(self, ticker, df):
        """
        執行 8+1 條件判定 (FR-04, FR-06)
        """
        # 取最新一筆資料
        row = df.iloc[-1]
        
        # 使用 Adj Close 或 Close，並強制轉為原生 float
        raw_price = row['Adj Close'] if 'Adj Close' in row else row['Close']
        price = float(raw_price) if not pd.isna(raw_price) else 0.0
        
        results = {}
        
        # === FR-06: 流動性檢查 ===
        # 使用 bool() 強制轉為 Python 原生布林值
        is_liquid = bool(row['Vol_SMA_20'] >= config.MIN_AVG_VOLUME_SHARES)
        
        # === FR-04: 8大技術條件 (全部套用 bool() 轉型) ===
        # C1: 價格 > 150 > 200
        results['c1_trend_stack'] = bool((price > row['SMA_150']) and (row['SMA_150'] > row['SMA_200']))
        
        # C2: 150 > 200
        results['c2_long_term'] = bool(row['SMA_150'] > row['SMA_200'])
        
        # C3: 200MA 向上
        results['c3_ma200_slope'] = bool(row['SMA_200'] > row['SMA_200_Prev'])
        
        # C4: 50 > 150 & 200
        results['c4_mid_term'] = bool((row['SMA_50'] > row['SMA_150']) and (row['SMA_50'] > row['SMA_200']))
        
        # C5: 價格 > 50
        results['c5_momentum'] = bool(price > row['SMA_50'])
        
        # C6: 高於低點 30%
        # 處理 Low_52W 可能為 NaN 的情況
        if pd.isna(row['Low_52W']):
            results['c6_support'] = False
        else:
            c6_threshold = row['Low_52W'] * config.DIST_FROM_LOW_THRESHOLD
            results['c6_support'] = bool(price >= c6_threshold)
        
        # C7: 在高點 25% 內
        if pd.isna(row['High_52W']):
            results['c7_resistance'] = False
        else:
            c7_threshold = row['High_52W'] * config.DIST_FROM_HIGH_THRESHOLD
            results['c7_resistance'] = bool(price >= c7_threshold)
        
        # C8: RS > 70
        # 處理 RS_Rating 可能為 NaN 的情況
        rs_val = row['RS_Rating']
        if pd.isna(rs_val):
            rs_val = 0
        results['c8_rs_strength'] = bool(rs_val >= config.RS_THRESHOLD)
        
        # 計算總分 (True 會被視為 1)
        technical_score = sum(results.values())
        
        # 判定狀態
        status = "FAIL"
        fail_reason = ""
        
        if not is_liquid:
            fail_reason = "Liquidity (Low Volume)"
        elif technical_score == 8:
            status = "PASS"
        else:
            # 找出第一個失敗的原因
            for k, v in results.items():
                if not v:
                    fail_reason = k
                    break
        
        # === 數值防呆處理 (針對 JSON 輸出) ===
        # 處理成交量 NaN
        vol_avg = row['Vol_SMA_20']
        if pd.isna(vol_avg):
            vol_avg = 0
            
        # 處理 52週距離顯示 NaN
        dist_low_str = "N/A"
        if not pd.isna(row['Low_52W']) and row['Low_52W'] != 0:
            dist_low_str = f"{((price - row['Low_52W'])/row['Low_52W'])*100:.1f}%"
            
        dist_high_str = "N/A"
        if not pd.isna(row['High_52W']) and row['High_52W'] != 0:
            dist_high_str = f"{((price - row['High_52W'])/row['High_52W'])*100:.1f}%"

        return {
            "ticker": ticker,
            "price": round(price, 2),
            "rs_rating": int(rs_val),  # 強制轉為原生 int
            "vol_avg": int(vol_avg),   # 強制轉為原生 int
            "status": status,
            "fail_reason": fail_reason,
            "match_count": f"{technical_score}/8",
            "details": results,        # 這裡面的 value 已經都被轉為原生 bool 了
            "dist_low_pct": dist_low_str,
            "dist_high_pct": dist_high_str
        }

class ReportGenerator:
    def generate(self, validation_results):
        """
        生成 CSV 與 JSON (FR-05)
        """
        # 1. JSON
        json_path = os.path.join(config.OUTPUT_DIR, "results.json")
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(validation_results, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"JSON 生成失敗: {e}")
            # 如果還是失敗，嘗試用 default=str 強制轉換
            with open(json_path, "w", encoding="utf-8") as f:
                 json.dump(validation_results, f, ensure_ascii=False, indent=2, default=str)
            
        # 2. CSV
        # 扁平化資料
        csv_data = []
        for res in validation_results:
            row = {
                "Ticker": res['ticker'],
                "Price": res['price'],
                "Status": res['status'],
                "Reason": res['fail_reason'],
                "Score": res['match_count'],
                "RS": res['rs_rating'],
                "Volume_Avg": res['vol_avg'],
                "Dist_Low": res['dist_low_pct'],
                "Dist_High": res['dist_high_pct']
            }
            # 加入細節 boolean
            for k, v in res['details'].items():
                row[k] = v
            csv_data.append(row)
            
        if csv_data:
            df = pd.DataFrame(csv_data)
            csv_path = os.path.join(config.OUTPUT_DIR, "results.csv")
            df.to_csv(csv_path, index=False, encoding="utf-8-sig") # sig for Excel zh-TW
            print(f"報告已生成:\n - {json_path}\n - {csv_path}")
            
            # 顯示簡單統計
            pass_count = len([r for r in validation_results if r['status'] == "PASS"])
            print(f"\n篩選完成！共 {len(validation_results)} 檔，合格: {pass_count} 檔。")
        else:
            print("\n沒有產生任何結果數據。")