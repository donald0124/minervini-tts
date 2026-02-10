# Product Requirements Document (PRD)
**Project Name:** MTTS Frontend Dashboard
**Version:** 1.0
**Status:** Draft
**Dependency:** Backend JSON Output (results.json)

---

## 1. Introduction (簡介)
### 1.1 Purpose (目的)
本專案為 Minervini 趨勢樣板選股系統的前端儀表板。目標是將後端運算產出的 JSON 數據，轉化為一個可互動、易於閱讀的網頁介面。使用者可以透過此介面快速篩選「合格 (PASS)」的股票，查看詳細技術指標，並一鍵跳轉至 TradingView 進行圖表分析。

### 1.2 Scope (範圍)
- **輸入來源：** 讀取後端生成的 `results.json` 靜態檔案。
- **主要功能：** 資料表格展示、關鍵字搜尋、欄位排序、狀態篩選、TradingView 連結整合。
- **技術建議：** React.js + Tailwind CSS + TanStack Table (或簡單的 HTML/JS 搭配 DataTables)。

---

## 2. Functional Requirements (功能需求 - FR)

### FR-01: Data Ingestion (資料載入)
- **來源：** 系統需非同步 (Async) 讀取 `results.json`。
- **錯誤處理：** 若無法讀取檔案或 JSON 格式錯誤，需在頁面顯示「無法載入數據，請確認後端是否執行完畢」的提示。
- **更新時間：** 需顯示資料生成的最後時間（可讀取 JSON 檔案的 Metadata 或由後端在 JSON 內放入 timestamp 欄位）。

### FR-02: Interactive Data Table (互動式表格)
表格需呈現以下欄位，並支援 RWD (響應式設計)：

| 欄位名稱 | 資料來源 (JSON key) | 顯示邏輯 / 格式 |
| :--- | :--- | :--- |
| **代號** | `ticker` | 顯示如 `2330` (去除 .TW 後綴)，**可點擊** (見 FR-04) |
| **名稱** | `name` | 若 JSON 有則直接顯示；若無則需前端維護 Mapping 表* |
| **價格** | `price` | 顯示數值，靠右對齊 |
| **狀態** | `status` | **PASS** (綠色標籤) / **FAIL** (紅色標籤) |
| **RS 分數** | `rs_rating` | 顯示 0-99，若 >=90 顯示高亮色 |
| **符合數** | `match_count` | 顯示如 `8/8` |
| **均量** | `vol_avg` | 格式化為 `K` 或 `M` (例：500,000 -> 500K) |
| **失敗原因** | `fail_reason` | 若 Status 為 FAIL，顯示主要原因；若 PASS 則留空 |

> *註：後端 SDD 定義 JSON 包含 `name`。若後端未實作，前端需額外透過 `twstock` 清單或靜態檔對應。*

### FR-03: Sorting & Filtering (排序與篩選)
- **預設排序：** 優先顯示 `Status = PASS`，其次依 `RS Rating` 由高至低排序。
- **使用者排序：** 點擊表頭可針對「價格」、「RS 分數」、「成交量」進行 升序/降序 切換。
- **快速篩選：**
  - **Toggle Switch:** 「只顯示合格股票 (Show PASS Only)」。
  - **Search Bar:** 可輸入代號 (e.g., 2330) 或名稱 (e.g., 台積電) 進行即時過濾。

### FR-04: TradingView Integration (圖表連動)
- **觸發點：** 點擊表格中的「股票代號」。
- **行為：** 開啟新分頁 (New Tab) 前往 TradingView。
- **網址轉換邏輯：** 必須處理台股代號後綴以符合 TradingView 格式。
  - **上市 (.TW):** `2330.TW` -> `TWSE:2330`
  - **上櫃 (.TWO):** `8069.TWO` -> `TPEX:8069`
  - **URL 範本：** `https://www.tradingview.com/chart/?symbol={MARKET}:{CODE}`

### FR-05: System Metadata Display (系統資訊)
在 Dashboard 頂部或側邊欄顯示：
1.  **資料更新時間：** 顯示後端最近一次執行的時間點。
2.  **趨勢模板參數 (Config)：** 顯示當前篩選標準，讓使用者知道依據為何。
    - *範例：* "RS > 70, Price > 200MA, Vol > 500K"
    - 此資訊可由前端寫死 (Hardcode) 或讀取後端輸出的 `meta` 欄位 (若有)。

---

## 3. UI/UX Guidelines (介面規範)

### 3.1 Layout (佈局)
- **Header:** 專案標題 (MTTS)、更新時間、參數摘要。
- **Main:** 控制列 (搜尋框、篩選開關) + 數據表格。
- **Footer:** 版權資訊或 GitHub 連結。

### 3.2 Visual Cues (視覺提示)
- **合格 (PASS):** 使用綠色系背景或文字 (e.g., Tailwind `bg-green-100 text-green-800`)。
- **不合格 (FAIL):** 使用灰色或淡紅色，降低視覺干擾。
- **趨勢強 (RS >= 90):** 使用金色或粗體強調，標示為強勢股。

---

## 4. Technical Implementation Notes (實作筆記)

### 4.1 Stock Name Mapping (若後端無名稱)
若 JSON 中 `name` 欄位為空，前端需準備一份 `stocks_map.js`：
```javascript
const stockMap = {
  "2330": "台積電",
  "2454": "聯發科",
  // ...
};
```

*建議：優先請後端在 JSON 中補齊 `name` 與 `sector` 欄位。*


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