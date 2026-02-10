from . import config
import pandas as pd
import json
import csv
import os
import numpy as np
from datetime import datetime, timezone, timedelta

class MinerviniValidator:
    def validate(self, ticker, name, df):
        """
        執行 8+1 條件判定 (FR-04, FR-06)
        並輸出關鍵價位供檢視
        """
        # 取最新一筆資料
        row = df.iloc[-1]
        
        # 使用 Adj Close 或 Close，並強制轉為原生 float
        raw_price = row['Adj Close'] if 'Adj Close' in row else row['Close']
        price = float(raw_price) if not pd.isna(raw_price) else 0.0
        
        # === 提取關鍵指標數值 (Handling NaN) ===
        def get_val(key, default=0.0):
            val = row.get(key, default)
            return float(val) if not pd.isna(val) else default

        sma_50 = get_val('SMA_50')
        sma_150 = get_val('SMA_150')
        sma_200 = get_val('SMA_200')
        sma_200_prev = get_val('SMA_200_Prev')
        low_52w = get_val('Low_52W')
        high_52w = get_val('High_52W')
        
        results = {}
        
        # === FR-06: 流動性檢查 ===
        is_liquid = bool(row['Vol_SMA_20'] >= config.MIN_AVG_VOLUME_SHARES)
        
        # === FR-04: 8大技術條件 ===
        # C1: 價格 > 150 > 200
        results['c1_trend_stack'] = bool((price > sma_150) and (sma_150 > sma_200))
        
        # C2: 150 > 200
        results['c2_long_term'] = bool(sma_150 > sma_200)
        
        # C3: 200MA 向上
        results['c3_ma200_slope'] = bool(sma_200 > sma_200_prev)
        
        # C4: 50 > 150 & 200
        results['c4_mid_term'] = bool((sma_50 > sma_150) and (sma_50 > sma_200))
        
        # C5: 價格 > 50
        results['c5_momentum'] = bool(price > sma_50)
        
        # C6: 高於低點 30%
        if pd.isna(row['Low_52W']):
            results['c6_support'] = False
        else:
            c6_threshold = low_52w * config.DIST_FROM_LOW_THRESHOLD
            results['c6_support'] = bool(price >= c6_threshold)
        
        # C7: 在高點 25% 內
        if pd.isna(row['High_52W']):
            results['c7_resistance'] = False
        else:
            c7_threshold = high_52w * config.DIST_FROM_HIGH_THRESHOLD
            results['c7_resistance'] = bool(price >= c7_threshold)
        
        # C8: RS > 70
        rs_val = row['RS_Rating']
        if pd.isna(rs_val):
            rs_val = 0
        results['c8_rs_strength'] = bool(rs_val >= config.RS_THRESHOLD)
        
        # 計算總分
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
        
        # === 數值防呆處理 ===
        vol_avg = row['Vol_SMA_20']
        if pd.isna(vol_avg):
            vol_avg = 0
            
        dist_low_str = "N/A"
        if low_52w != 0:
            dist_low_str = f"{((price - low_52w)/low_52w)*100:.1f}%"
            
        dist_high_str = "N/A"
        if high_52w != 0:
            dist_high_str = f"{((price - high_52w)/high_52w)*100:.1f}%"

        return {
            "ticker": ticker,
            "name": name,
            "price": round(price, 2),
            "rs_rating": int(rs_val),
            "vol_avg": int(vol_avg),
            "status": status,
            "fail_reason": fail_reason,
            "match_count": f"{technical_score}/8",
            "details": results,
            "dist_low_pct": dist_low_str,
            "dist_high_pct": dist_high_str,
            # 新增：關鍵指標數值 (供前端或報表檢視用)
            "indicators": {
                "SMA_50": round(sma_50, 2),
                "SMA_150": round(sma_150, 2),
                "SMA_200": round(sma_200, 2),
                "SMA_200_Prev": round(sma_200_prev, 2),
                "High_52W": round(high_52w, 2),
                "Low_52W": round(low_52w, 2)
            }
        }

class ReportGenerator:
    def generate(self, validation_results):
        """
        生成 CSV 與 JSON (FR-05)
        JSON 結構變更為包含 metadata
        """
        # 設定台灣時區 (UTC+8)
        tw_tz = timezone(timedelta(hours=8))
        current_time = datetime.now(tw_tz).isoformat()

        # 1. 準備 Metadata
        output_data = {
            "metadata": {
                "timestamp": current_time,
                "config": {
                    "rs_threshold": config.RS_THRESHOLD,
                    "min_volume": config.MIN_AVG_VOLUME_SHARES,
                    "dist_low_pct": config.DIST_FROM_LOW_THRESHOLD,
                    "dist_high_pct": config.DIST_FROM_HIGH_THRESHOLD,
                    "ma_slope_lookback": config.MA_SLOPE_LOOKBACK
                }
            },
            "data": validation_results
        }

        # 2. JSON 輸出
        json_path = os.path.join(config.OUTPUT_DIR, "results.json")
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"JSON 生成失敗: {e}")
            with open(json_path, "w", encoding="utf-8") as f:
                 json.dump(output_data, f, ensure_ascii=False, indent=2, default=str)
            
        # 3. CSV 輸出 (保持扁平化，增加 Name 與 Indicators 欄位)
        csv_data = []
        for res in validation_results:
            row = {
                "Ticker": res['ticker'],
                "Name": res['name'],
                "Price": res['price'],
                "Status": res['status'],
                "Reason": res['fail_reason'],
                "Score": res['match_count'],
                "RS": res['rs_rating'],
                "Volume_Avg": res['vol_avg'],
                "Dist_Low": res['dist_low_pct'],
                "Dist_High": res['dist_high_pct']
            }
            # 加入條件細節 boolean
            for k, v in res['details'].items():
                row[k] = v
            
            # 加入關鍵指標數值
            for k, v in res['indicators'].items():
                row[k] = v
                
            csv_data.append(row)
            
        if csv_data:
            df = pd.DataFrame(csv_data)
            csv_path = os.path.join(config.OUTPUT_DIR, "results.csv")
            df.to_csv(csv_path, index=False, encoding="utf-8-sig")
            print(f"報告已生成:\n - {json_path}\n - {csv_path}")
            
            # 顯示簡單統計
            pass_count = len([r for r in validation_results if r['status'] == "PASS"])
            print(f"\n篩選完成！共 {len(validation_results)} 檔，合格: {pass_count} 檔。")
        else:
            print("\n沒有產生任何結果數據。")