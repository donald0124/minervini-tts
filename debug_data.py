import pandas as pd
import pickle
import glob
import os

# 設定 Cache 路徑
CACHE_FILE = glob.glob("backend/cache/*.pkl")
if not CACHE_FILE:
    print("❌ 找不到快取檔案，請先執行 manual_deploy.py")
    exit()

CACHE_PATH = CACHE_FILE[0]
print(f"📂 正在讀取快取: {CACHE_PATH}")

with open(CACHE_PATH, "rb") as f:
    data = pickle.load(f)

# 請輸入有問題的股票代碼 (例如 2330.TW)
target_ticker = input("請輸入有問題的股票代碼 (例如 2330.TW): ").strip().upper()

if target_ticker not in data.columns.levels[0]:
    print(f"❌ 快取中找不到 {target_ticker} 的資料。")
    print("可能原因：下載時失敗，或者代碼輸入錯誤 (請確認 .TW 或 .TWO)")
else:
    df = data[target_ticker]
    # 移除空值行
    df = df.dropna(how='all')
    
    print(f"\n📊 {target_ticker} 數據診斷：")
    print(f"--------------------------------")
    print(f"資料總筆數 (Rows): {len(df)}")
    
    if len(df) > 0:
        print(f"資料起始日: {df.index[0].date()}")
        print(f"資料結束日: {df.index[-1].date()}")
        
        # 檢查關鍵欄位
        close_price = df['Close'].iloc[-1]
        print(f"最新收盤價: {close_price}")
        
        if len(df) < 200:
            print(f"⚠️ 警告：資料長度不足 200 筆 (只有 {len(df)} 筆)！")
            print("   -> 這就是為什麼 200MA 為 0.0 的原因。")
            print("   -> 原因可能是：1. 新上市股票 (IPO 不滿一年)  2. Yahoo 下載被截斷")
        else:
            print("✅ 資料長度足夠 (>200)，均線應該要能計算。")
    else:
        print("⚠️ 警告：該股票有欄位，但內容全是空的 (Empty Data)。")