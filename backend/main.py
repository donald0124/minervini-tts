import sys
import os

# 將 src 加入 path 以便 import
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.fetcher import StockFetcher
from src.processor import DataProcessor
from src.validator import MinerviniValidator, ReportGenerator

def main():
    print("=== Minervini Trend Template Screener (MTTS) 啟動 ===")
    
    # 1. 初始化模組
    fetcher = StockFetcher()
    processor = DataProcessor()
    validator = MinerviniValidator()
    reporter = ReportGenerator()
    
    # 2. 獲取清單 (Universe)
    tickers = fetcher.get_universe()
    
    # 測試模式：為了省時間，您可以先只跑前 50 檔測試
    tickers = tickers[:200] 
    
    # 3. 獲取數據 (Fetch)
    raw_data = fetcher.fetch_batch(tickers)
    
    if raw_data is None or raw_data.empty:
        print("無法獲取數據，程式終止。")
        return

    # 4. 處理數據與計算指標 (Process & RS)
    stock_map = processor.process_data(raw_data, tickers)
    
    # 5. 驗證策略 (Validate)
    results = []
    print("正在執行策略驗證...")
    for ticker, df in stock_map.items():
        res = validator.validate(ticker, df)
        results.append(res)
        
    # 6. 生成報告 (Report)
    reporter.generate(results)

if __name__ == "__main__":
    main()