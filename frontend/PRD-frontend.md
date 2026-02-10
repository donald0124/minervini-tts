# Product Requirements Document (PRD)
**Project Name:** MTTS Frontend Dashboard
**Version:** 1.1 (Backend-Driven Update)
**Status:** Ready for Dev
**Dependency:** Backend JSON Output (`results.json`)

---

## 1. Introduction (簡介)
### 1.1 Purpose (目的)
本專案為 Minervini 趨勢樣板選股系統的前端儀表板。目標是將後端運算產出的 JSON 數據，轉化為一個可互動、易於閱讀的網頁介面。系統強調「數據驅動」，介面上的篩選標準與股票資訊皆由後端動態提供，確保前後端資訊一致。

### 1.2 Scope (範圍)
- **輸入來源：** 讀取後端生成的 `results.json` 靜態檔案。
- **主要功能：** 資料表格展示、關鍵字搜尋、多欄位排序、狀態篩選、TradingView 圖表連動、系統參數顯示。
- **技術建議：** React.js + Tailwind CSS + TanStack Table (或類似的高效能表格套件)。

---

## 2. Functional Requirements (功能需求 - FR)

### FR-01: Data Ingestion (資料載入與結構解析)
- **來源：** 系統需非同步 (Async) 讀取 `results.json`。
- **結構變更支援：** 支援讀取包含 `metadata` 與 `data` 的根物件結構。
- **錯誤處理：** 若無法讀取檔案或 JSON 格式錯誤，需顯示友善錯誤訊息 (e.g., "資料同步中或尚未生成")。
- **系統資訊顯示 (Metadata)：**
    - 從 `metadata.timestamp` 讀取並顯示「最後更新時間」。
    - 從 `metadata.config` 讀取並顯示當次篩選使用的參數（RS 門檻、成交量標準等）。

### FR-02: Interactive Data Table (互動式表格)
表格需讀取 JSON 中的 `data` 陣列，呈現以下欄位：

| 欄位名稱 | 資料來源 (JSON key) | 顯示邏輯 / 格式 |
| :--- | :--- | :--- |
| **代號** | `ticker` | 顯示如 `2330` (去除 .TW 後綴)，**可點擊** (見 FR-04) |
| **名稱** | `name` | **直接顯示後端提供的值** (e.g., "台積電") |
| **價格** | `price` | 顯示數值，靠右對齊，建議保留小數點後 1-2 位 |
| **狀態** | `status` | **PASS** (綠色標籤) / **FAIL** (紅色/灰色標籤) |
| **RS 分數** | `rs_rating` | 顯示 0-99，若 >=90 建議使用強調色 (如金色/粗體) |
| **符合數** | `match_count` | 顯示如 `8/8` |
| **均量** | `vol_avg` | 需格式化縮寫 (例：`500,000` -> `500K` 或 `0.5M`) |
| **失敗原因** | `fail_reason` | 若 Status 為 FAIL，顯示主要原因；若 PASS 則留空 |
| **離低點** | `dist_low_pct` | 顯示如 `28.3%` (滑鼠 Hover 可顯示 Tooltip: "52週低點距離") |
| **離高點** | `dist_high_pct` | 顯示如 `-4.6%` |

### FR-03: Sorting & Filtering (排序與篩選)
- **預設排序：** 載入時，優先顯示 `Status = PASS`，次級排序依 `RS Rating` (高->低)。
- **使用者排序：** 支援點擊表頭切換以下欄位的 升/降序：
    - 價格 (`price`)
    - RS 分數 (`rs_rating`)
    - 成交量 (`vol_avg`)
    - 離低點/高點幅度
- **快速篩選 (Filter)：**
  - **Toggle Switch:** 「只顯示合格股票 (Show PASS Only)」。
  - **Search Bar:** 支援全域搜尋，輸入關鍵字可同時匹配 `ticker` (代號) 與 `name` (名稱)。

### FR-04: TradingView Integration (圖表連動)
- **觸發點：** 點擊表格中的「股票代號」或「名稱」。
- **行為：** 開啟新分頁 (New Tab) 前往 TradingView。
- **網址轉換邏輯：** 必須處理台股代號後綴以符合 TradingView 格式。
  - **上市 (.TW):** `2330.TW` -> `TWSE:2330`
  - **上櫃 (.TWO):** `8069.TWO` -> `TPEX:8069`
  - **URL 範本：** `https://www.tradingview.com/chart/?symbol={MARKET}:{CODE}`

### FR-05: Dashboard Header & Info (儀表板資訊列)
在頁面頂部需動態呈現由後端 `metadata.config` 提供的篩選標準，而非前端寫死：

* **Display Logic:**
    * RS 門檻: `metadata.config.rs_threshold` (e.g., "RS > 70")
    * 成交量門檻: `metadata.config.min_volume` (e.g., "Vol > 500K")
    * 上市天數: `metadata.config.ipo_min_days` (Optional)

---

## 3. UI/UX Guidelines (介面規範)

### 3.1 Layout (佈局)
- **Header:**
    - 左側：專案標題 (MTTS Dashboard)
    - 右側：最後更新時間 (YYYY-MM-DD HH:MM)
    - 下方：參數摘要 Tag (e.g., `[RS>70]`, `[Vol>500K]`)
- **Main Content:**
    - 工具列：搜尋框 (Search)、只看合格開關 (Switch)
    - 數據表格：RWD 設計 (手機版可隱藏次要欄位如「離高/低點」)
- **Footer:** 簡單版權資訊。

### 3.2 Visual Cues (視覺提示)
- **Status Colors:**
    - PASS: `bg-green-100 text-green-800` (Tailwind)
    - FAIL: `bg-red-50 text-red-600`
- **Rows:** 建議使用斑馬紋 (Zebra striping) 或 Hover 效果增加閱讀性。
- **Loading State:** 在讀取 JSON 時顯示 Skeleton Loader 或 Loading Spinner。

---

## 4. Technical Implementation Notes (實作筆記)

### 4.1 JSON Fetching Strategy
```javascript
// 範例 Fetch 邏輯
useEffect(() => {
  fetch('/backend/results.json') // 假設路徑
    .then(res => res.json())
    .then(jsonData => {
      setMetadata(jsonData.metadata);
      setData(jsonData.data);
    })
    .catch(err => console.error("Failed to load data", err));
}, []);
```

### 4.2 TradingView Link Helper
```JavaScript

function getTradingViewUrl(ticker) {
  // 輸入 ticker 格式預期為 "2330.TW" 或 "8069.TWO"
  const code = ticker.split('.')[0];
  let market = 'TWSE'; // 預設上市
  
  if (ticker.includes('.TWO')) {
    market = 'TPEX'; // 上櫃
  }
  
  return `https://www.tradingview.com/chart/?symbol=${market}:${code}`;
}
```
### 4.3 Detail View (Optional / Nice to have)
若表格過於擁擠，可設計「點擊行 (Row)」展開詳細資訊，顯示 8 大條件的個別 Pass/Fail 細節 (讀取 JSON 中的 `details` 物件)。

### 4.4 Number Formatting
使用 `Intl.NumberFormat` 處理成交量與價格，確保千分位顯示 (e.g., `1,234.5`)。

成交量縮寫邏輯：若 `> 1,000,000` 顯示 `1.2M`；若 `> 1,000` 顯示 `1.2K`。


---

## 5. Acceptance Criteria (驗收標準 - UAT)

### 5.1 資料整合測試
- [ ] **資料載入：** 前端能成功讀取 `results.json`，且頁面頂部正確顯示 `metadata.timestamp` 的更新時間。
- [ ] **參數同步：** 頁面顯示的篩選條件（如 "RS > 70"）需與 JSON 內的 `metadata.config` 一致，而非前端寫死。
- [ ] **錯誤處理：** 若移除 `results.json` 或破壞 JSON 格式，頁面需顯示友善的錯誤提示，而非白畫面。

### 5.2 互動功能測試
- [ ] **外部連結：** 隨機點擊 3 檔「上市」與 3 檔「上櫃」股票，確認皆能正確開啟 TradingView 對應技術線圖（代號格式需正確轉換）。
- [ ] **篩選功能：** 開啟「只顯示合格股票 (Show PASS Only)」開關後，表格內**不應出現**任何 `Status = FAIL` 的列。
- [ ] **排序功能：** 點擊「RS 分數」表頭，確認資料能由大至小（降序）與由小至大（升序）正確排列。

### 5.3 介面呈現測試
- [ ] **RWD 測試：** 在手機尺寸 (Width < 768px) 下，表格應能橫向捲動或自動隱藏次要欄位（如「離高/低點」），版面不跑版。
- [ ] **格式檢查：** 成交量是否已正確縮寫（如 `15,000,000` -> `15M` 或 `15,000K`）。

---

## 6. Future Roadmap (未來規劃 - v1.2+)

### 6.1 視覺化增強
- **K 線圖預覽 (Chart Preview):** 滑鼠懸停 (Hover) 於股票代號時，顯示簡易的 SVG 走勢圖或 TradingView Lightweight Chart。
- **歷史趨勢 (Historical Data):** 整合後端歷史存檔，允許使用者透過下拉選單切換查看「過去某一天」的篩選結果。

### 6.2 進階功能
- **自訂篩選 (Custom Filter):** 允許使用者在前端動態調整篩選標準（例如：臨時想找 RS > 90 的股票），而非僅依賴後端設定。
- **關注清單 (Watchlist):** 利用 Browser LocalStorage 實作「我的最愛」功能，將感興趣的股票釘選在表格最上方。