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
    
    # 2. 獲取清單 (Universe) - 這裡會回傳 {代號: 名稱} 的 Dictionary
    tickers_map = fetcher.get_universe()
    
    # 轉換為列表供下載用
    ticker_list = list(tickers_map.keys())
    
    # 測試模式：為了省時間，您可以先只跑前 200 檔測試
    # 如果要跑全市場，請註解掉下面這行
    ticker_list = ticker_list[:100]
    
    # 3. 獲取數據 (Fetch)
    raw_data = fetcher.fetch_batch(ticker_list)
    
    if raw_data is None or raw_data.empty:
        print("無法獲取數據，程式終止。")
        return

    # 4. 處理數據與計算指標 (Process & RS)
    stock_map = processor.process_data(raw_data, ticker_list)
    
    # 5. 驗證策略 (Validate)
    results = []
    print("正在執行策略驗證...")
    for ticker, df in stock_map.items():
        # 從 map 中獲取中文名稱，若找不到則給空字串
        stock_name = tickers_map.get(ticker, "")
        
        # 傳入 ticker, name, df
        res = validator.validate(ticker, stock_name, df)
        results.append(res)
        
    # 6. 生成報告 (Report)
    reporter.generate(results)

if __name__ == "__main__":
    main()