# System Design Document (SDD) - Frontend
**Project Name:** MTTS Frontend Dashboard
**Version:** 1.0
**Date:** 2026-02-10
**Author:** AI Assistant / User

---

## 1. 系統概述 (System Overview)

### 1.1 目標
建構一個輕量級、高效能的單頁應用程式 (SPA)，用於呈現 Minervini 選股系統的後端數據。系統強調「數據驅動 UI」，所有篩選標準與股票資訊皆依賴後端 `results.json`，前端僅負責渲染與互動。

### 1.2 技術堆疊 (Tech Stack)
* **核心框架:** React 18+ (使用 Vite 建置)
* **語言:** TypeScript (強烈建議，以確保 JSON 資料結構型別安全)
* **樣式庫:** Tailwind CSS (快速刻板、響應式設計)
* **表格核心:** TanStack Table v8 (Headless UI，處理排序、篩選、分頁)
* **圖標庫:** Lucide React (輕量級 Icon)
* **資料獲取:** Native Fetch API (搭配 `useEffect`)

---

## 2. 系統架構 (System Architecture)

### 2.1 資料流 (Data Flow)
系統採用單向資料流，由頂層組件獲取資料後向下傳遞。

1.  **Fetch:** 應用程式啟動時，`App` 組件非同步請求 `/backend/results.json`。
2.  **Parse:** 解析 JSON，分離 `metadata` (設定資訊) 與 `data` (股票清單)。
3.  **Distribute:**
    * 將 `metadata` 傳遞給 `Header` 組件顯示更新時間與參數。
    * 將 `data` 傳遞給 `Dashboard` -> `StockTable` 進行列表渲染。
4.  **Interact:** 使用者操作篩選/排序 -> TanStack Table 重新計算顯示內容 -> UI 更新。

### 2.2 目錄結構 (Directory Structure)

    src/
        components/
            Header.tsx          # 頂部資訊列 (顯示 Metadata)
            Dashboard.tsx       # 主要容器
            StockTable.tsx      # 核心表格 (TanStack Table 實作)
            FilterBar.tsx       # 搜尋框與開關
            StatusBadge.tsx     # 狀態標籤 (PASS/FAIL)
        types/
            schema.ts           # TypeScript 介面定義
        utils/
            formatters.ts       # 數字格式化 (K/M, %)
            links.ts            # TradingView 網址轉換邏輯
        App.tsx                 # 資料載入入口
        main.tsx

---

## 3. 資料結構定義 (Data Schema)

在 `src/types/schema.ts` 中定義與後端一致的介面。

    interface Config {
        rs_threshold: number;
        min_volume: number;
        dist_low_pct: number;
        dist_high_pct: number;
        ma_slope_lookback: number;
    }

    interface Metadata {
        timestamp: string;
        config: Config;
    }

    interface StockData {
        ticker: string;
        name: string;
        price: number;
        rs_rating: number;
        vol_avg: number;
        status: "PASS" | "FAIL";
        fail_reason: string;
        match_count: string;
        details: Record<string, boolean>;
        dist_low_pct: string;
        dist_high_pct: string;
    }

    interface APIResponse {
        metadata: Metadata;
        data: StockData[];
    }

---

## 4. 組件設計 (Component Design)

### 4.1 App Component (Entry Point)
* **職責:** 負責 Data Fetching 與 Loading/Error 狀態管理。
* **狀態:**
    * `loading`: boolean
    * `error`: string | null
    * `payload`: APIResponse | null
* **邏輯:** 使用 `useEffect` 在 mount 時呼叫 `fetch('/results.json')`。

### 4.2 Header Component
* **職責:** 顯示系統標題、最後更新時間、篩選參數摘要。
* **Props:** `metadata: Metadata`
* **呈現:**
    * 更新時間：使用 `new Date(timestamp).toLocaleString()` 格式化。
    * 參數標籤：使用 Tailwind Badge 樣式顯示 `RS > {config.rs_threshold}`, `Vol > {config.min_volume}`。

### 4.3 StockTable Component (Core)
* **職責:** 整合 TanStack Table，處理排序、篩選、分頁與 RWD 顯示。
* **Props:** `data: StockData[]`, `showPassOnly: boolean`, `globalFilter: string`
* **Table Columns 定義:**
    1.  **代號/名稱:** 組合欄位，點擊觸發 `openTradingView(original.ticker)`。
    2.  **價格:** 靠右對齊，格式化千分位。
    3.  **狀態:** 渲染 `StatusBadge` 組件。
    4.  **RS:** 依數值顯示顏色 (>=90 金色, <70 灰色)。
    5.  **均量:** 使用 `formatVolume` 函數。
    6.  **離低/高點:** 手機版隱藏 (`hidden md:table-cell`)。

### 4.4 FilterBar Component
* **職責:** 提供使用者互動介面。
* **輸出:**
    * `onSearchChange(val: string)`
    * `onTogglePassOnly(checked: boolean)`

---

## 5. 關鍵邏輯實作 (Key Implementation Logic)

### 5.1 TradingView 連結轉換 (utils/links.ts)
處理台股代號後綴，轉換為 TradingView 支援的格式。

    export function getTradingViewUrl(ticker: string): string {
        // 移除後綴並判斷市場
        const code = ticker.split('.')[0];
        let market = 'TWSE'; // 預設上市
    
        if (ticker.includes('.TWO')) {
            market = 'TPEX'; // 上櫃
        }
    
        return `https://www.tradingview.com/chart/?symbol=${market}:${code}`;
    }

### 5.2 數值格式化 (utils/formatters.ts)
處理成交量縮寫 (K/M)。

    export function formatVolume(val: number): string {
        if (val >= 1000000) {
            return (val / 1000000).toFixed(1) + 'M';
        }
        if (val >= 1000) {
            return (val / 1000).toFixed(1) + 'K';
        }
        return val.toString();
    }

### 5.3 模糊搜尋邏輯 (Table Filter)
TanStack Table 的 `globalFilter` 預設僅支援純文字。需自訂過濾函數以同時搜尋代號與名稱。

    // 在 useReactTable 設定中
    globalFilterFn: (row, columnId, filterValue) => {
        const search = filterValue.toLowerCase();
        const ticker = row.original.ticker.toLowerCase();
        const name = row.original.name.toLowerCase();
        return ticker.includes(search) || name.includes(search);
    }

---

## 6. UI/UX 規範細節

### 6.1 色彩計畫 (Tailwind Classes)
* **背景:** `bg-gray-50` (整體背景), `bg-white` (卡片/表格背景)
* **PASS 狀態:** `bg-green-100 text-green-800 border-green-200`
* **FAIL 狀態:** `bg-gray-100 text-gray-600` (若為次要) 或 `bg-red-50 text-red-600` (若需強調)
* **RS 強勢:** `font-bold text-amber-600` (當 RS >= 90)

### 6.2 響應式斷點 (Breakpoints)
* **Mobile (< 768px):**
    * 隱藏欄位：符合數、失敗原因、離低點、離高點。
    * 調整佈局：FilterBar 變為垂直堆疊。
* **Desktop (>= 768px):**
    * 顯示完整資訊表格。

---

## 7. 部署與整合 (Deployment)

* **Build:** 執行 `npm run build` 產出 `dist/` 資料夾。
* **整合:**
    * 由於是讀取靜態 JSON，前端 `dist/` 可與後端生成的 `results.json` 部署在同一 Web Server (如 Nginx/Vercel) 下。
    * 或者，後端 Python 腳本執行完畢後，將 JSON 複製到前端 `public/` 目錄下進行開發預覽。