import pandas as pd
import pickle
import glob

# 1. 讀取快取
files = glob.glob("backend/cache/*.pkl")
if not files:
    print("❌ 沒找到 .pkl 快取檔！請先跑 fetcher。")
    exit()

cache_file = files[0]
print(f"📂 正在檢查快取: {cache_file}")

with open(cache_file, "rb") as f:
    data = pickle.load(f)

# 2. 挑一檔「有問題」的股票來檢查 (例如剛剛均線是 0 的那檔)
target = input("請輸入一檔結果異常的股票代碼 (例如 2330.TW): ").strip().upper()

if target in data.columns.levels[0]:
    df = data[target].copy()
    # 移除全空行
    df.dropna(how='all', inplace=True)
    
    print(f"\n🔍 {target} 原始數據分析:")
    print(f"   - 總筆數 (Rows): {len(df)}")
    if len(df) > 0:
        print(f"   - 開始日期: {df.index[0].date()}")
        print(f"   - 結束日期: {df.index[-1].date()}")
        print(f"   - 收盤價預覽: {df['Close'].tail(3).values}")
        
        # 關鍵判斷
        if len(df) < 250:
            print(f"❌ 抓到了！數據長度不足 ({len(df)} < 250)。")
            print("   -> 這是 Fetcher 的問題。Yahoo 截斷了數據。")
        else:
            print(f"✅ 數據長度正常 ({len(df)} > 250)。")
            print("   -> Fetcher 沒問題，問題出在後面 (Processor/Validator)。")
    else:
        print("❌ 數據長度為 0！(Empty DataFrame)")
else:
    print(f"❌ 快取裡根本沒有 {target} 這檔股票。")