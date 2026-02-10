# 系統設計文件 (SDD)
**專案名稱：** Minervini 趨勢樣板選股系統 (MTTS)
**版本：** 1.1 (對應 PRD v1.1)
**狀態：** Final
**日期：** 2026-02-10
**作者：** AI Assistant / User

---

## 1. 簡介 (Introduction)

### 1.1 目的 (Purpose)
本文件旨在定義 MTTS 系統的技術架構與實作細節。系統核心目標為自動化 Mark Minervini 的《超級績效》選股策略，透過 Python 進行高效能的台股掃描，並解決流動性過濾與全市場相對強度 (RS) 排名運算問題。

### 1.2 設計原則 (Design Principles)
-   **可解釋性 (Explainability)：** 輸出結果需包含詳細的失敗原因與指標數值，而非僅有通過/失敗。
-   **效能 (Performance)：** 利用多執行緒 (Multi-threading) 與向量化運算 (Vectorization) 確保全市場掃描在 5 分鐘內完成。
-   **強健性 (Robustness)：** 具備 API 異常重試機制與地端快取，避免因網路問題中斷或被 Ban IP。

---

## 2. 系統架構 (System Architecture)

### 2.1 高層架構圖 (High-Level Architecture)
系統採用 **ETL (Extract, Transform, Load)** 管道架構，並引入 **快取層 (Caching Layer)** 以優化數據攝取。

```mermaid
graph TD
    subgraph "External Sources"
        TWSE[twstock Library]
        Yahoo[Yahoo Finance API]
    end

    subgraph "Data Layer (Fetcher)"
        Cache[(Local File Cache)]
        Fetcher[StockFetcher Module]
    end

    subgraph "Logic Layer (Core)"
        Filter[Liquidity Filter]
        RS_Engine[RS Ranking Engine (Global)]
        Tech_Engine[Technical Indicator Engine]
        Validator[Minervini Validator]
    end

    subgraph "Presentation Layer"
        CSV[CSV Reporter]
        JSON[JSON Reporter]
    end

    TWSE --> Fetcher
    Yahoo --> Fetcher
    Fetcher <--> Cache
    Fetcher --> Filter
    Filter --> RS_Engine
    RS_Engine --> Tech_Engine
    Tech_Engine --> Validator
    Validator --> CSV
    Validator --> JSON
```


### 2.2 技術堆疊 (Tech Stack)
-   **語言:** Python 3.10+
-   **數據源:** `yfinance` (股價數據), `twstock` (股票代碼與分類資訊)
-   **數據處理:** `pandas` (核心向量化運算), `numpy` (數值計算)
-   **並發處理:** `concurrent.futures.ThreadPoolExecutor` (加速 I/O)
-   **儲存格式:** `pickle` (二進位快取), `csv` (Excel 報表), `json` (結構化數據)

---

## 3. 模組設計 (Module Design)

### 3.1 `StockFetcher` (數據攝取模組)
負責與外部 API 溝通並管理本地快取。

-   **類別成員:**
    -   `CacheManager`: 負責讀寫 `./cache/market_data_YYYY-MM-DD.pkl`。
-   **主要方法:**
    -   `get_universe() -> List[str]`: 
        -   呼叫 `twstock` 取得所有代碼。
        -   **邏輯:** 過濾 `type='股票'`，並**排除** 00xx (ETF), 91xx (DR), 權證等非普通股。
    -   `fetch_batch(tickers) -> DataFrame`:
        -   檢查本日 Cache 是否存在。
        -   **Cache Miss:** 執行 `yf.download(tickers, period='1y', threads=True)`。
        -   **Cache Hit:** 直接從 Pickle 載入。
        -   **關鍵:** 處理 Multi-Index DataFrame，將資料正規化為標準 OHLCV 格式。

### 3.2 `DataProcessor` (數據處理與運算模組)
負責執行「雙重掃描」與指標計算邏輯。

-   **主要方法:**
    -   `filter_liquidity(df) -> DataFrame`:
        -   計算 20日均量 (`Volume_SMA_20`)。
        -   **邏輯:** 剔除 `Volume_SMA_20 < 500,000` (500張) 的股票。
        -   **IPO 檢查:** 剔除歷史資料長度 < 250 筆的標的。
    -   `calculate_global_rs(df) -> DataFrame`:
        -   **邏輯 (Pass 2):** 計算所有存活股票的 1 年 ROC (Rate of Change)。
        -   使用 `df['ROC_1Y'].rank(pct=True) * 99` 算出全市場 RS 分數 (0-99)。
    -   `add_technical_indicators(df) -> DataFrame`:
        -   計算 SMA (50, 150, 200)。
        -   計算 52W High (252天最高), 52W Low (252天最低)。
        -   計算 SMA_200 斜率 (比較今日與 22 天前數值)。

### 3.3 `MinerviniValidator` (策略驗證模組)
負責執行 8 大條件判定。

-   **輸入:** 單一股票的 `Series` (含所有計算後的指標)。
-   **輸出:** `ValidationResult` 物件 (Dict)。
-   **邏輯細節:**
    ```python
    def validate(row):
        results = {}
        # C1: Trend Stack (價格 > 150 > 200)
        results['c1'] = row['Close'] > row['SMA_150'] > row['SMA_200']
        # C2: Long Term Align (150 > 200)
        results['c2'] = row['SMA_150'] > row['SMA_200']
        # C3: Trend Slope (200MA 向上)
        results['c3'] = row['SMA_200'] > row['SMA_200_Prev']
        # C4: Medium Align (50 > 150 & 200)
        results['c4'] = row['SMA_50'] > row['SMA_150'] and row['SMA_50'] > row['SMA_200']
        # C5: Momentum (價格 > 50)
        results['c5'] = row['Close'] > row['SMA_50']
        # C6: Support (高於低點 30%)
        results['c6'] = row['Close'] >= (row['Low_52W'] * 1.30)
        # C7: Resistance (低於高點 25% 內)
        results['c7'] = row['Close'] >= (row['High_52W'] * 0.75)
        # C8: Relative Strength (RS >= 70)
        results['c8'] = row['RS_Rating'] >= 70
        
        # 計算總分
        score = sum(results.values())
        status = "PASS" if score == 8 else "FAIL"
        
        return {
            "ticker": row.name,
            "status": status, 
            "score": f"{score}/8",
            "details": results
        }
    ```

### 3.4 `ReportGenerator` (報告生成模組)
-   **方法:**
    -   `to_csv(data, filename)`: 將巢狀的驗證結果扁平化，生成易於 Excel 篩選的表格。
    -   `to_json(data, filename)`: 保留完整巢狀結構，供 Web 前端或 Dashboard 使用。

---

## 4. 資料流程 (Data Flow)

1.  **初始化 (Init):** 載入 `config.py` 設定 (RS 閾值, 流動性門檻, 輸出路徑)。
2.  **清單獲取 (Universe):** 從 `twstock` 取得 2000+ 檔代碼，過濾後剩餘約 1700 檔普通股。
3.  **數據下載 (Fetch - Pass 0):** 檢查 Cache，若無則並發下載 1 年歷史數據。
4.  **前處理 (Pre-process - Pass 1):** -   計算 20日均量，**剔除流動性不足** (< 500張) 的股票。
    -   剔除歷史長度 < 250 天 (IPO) 的股票。
5.  **RS 運算 (RS Ranking - Pass 2):** 針對剩餘存活股票計算 ROC 並排序，填入 `RS_Rating`。
6.  **指標運算 (Technical Calc - Pass 3):** 計算 SMA, High/Low 等技術指標。
7.  **篩選 (Filter):** 逐一驗證 8 大條件。
8.  **輸出 (Output):** 生成 CSV 與 JSON 報表。

---

## 5. 資料結構設計 (Data Schema)

### 5.1 JSON 輸出結構 (API / Dashboard)
```json
[
  {
    "ticker": "2330.TW",
    "name": "台積電",
    "sector": "半導體業",
    "price": 600.0,
    "volume_avg": 35000000,
    "rs_rating": 92,
    "status": "PASS",
    "match_count": "8/8",
    "criteria_breakdown": {
      "c1_trend_stack": { "pass": true, "msg": "Price > 150MA > 200MA" },
      "c2_long_term": { "pass": true, "msg": "150MA > 200MA" },
      "c3_ma200_slope": { "pass": true, "val": 1.02 },
      "c4_mid_term": { "pass": true, "msg": "50MA > 150MA" },
      "c5_momentum": { "pass": true, "msg": "Price > 50MA" },
      "c6_support": { "pass": true, "value": "+45%", "threshold": ">30%" },
      "c7_resistance": { "pass": true, "value": "-5%", "threshold": "Within 25%" },
      "c8_rs_strength": { "pass": true, "value": 92, "threshold": ">=70" }
    }
  }
]
```

## 6. 設定檔規劃 (Configuration)

檔案：`config.py`

``` python
import os

# 核心篩選門檻
RS_THRESHOLD = 70               # 相對強度需大於 70 (前 30%)
MIN_AVG_VOLUME_SHARES = 500000  # 最小 20日均量 (500張)
IPO_MIN_DAYS = 250              # 最小上市天數 (排除新股)

# 技術型態參數
DIST_FROM_LOW_THRESHOLD = 1.30  # 需高於 52週低點 30%
DIST_FROM_HIGH_THRESHOLD = 0.75 # 需在 52週最高點 25% 範圍內 (1 - 0.25)
MA_SLOPE_LOOKBACK = 22          # 判斷 200MA 斜率的回看天數 (約1個月)

# 系統設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
MAX_WORKERS = 16                # 資料下載並發執行緒數量
```