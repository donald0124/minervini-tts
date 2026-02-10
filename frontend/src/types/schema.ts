export interface Config {
    rs_threshold: number;
    min_volume: number;
    dist_low_pct: number;
    dist_high_pct: number;
    ma_slope_lookback: number;
}

export interface Metadata {
    timestamp: string;
    config: Config;
}

// 新增 Indicators 介面
export interface Indicators {
    SMA_50: number;
    SMA_150: number;
    SMA_200: number;
    SMA_200_Prev: number;
    High_52W: number;
    Low_52W: number;
}

export interface StockData {
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
    // 新增此欄位
    indicators: Indicators;
}

export type APIResponse = {
    metadata: Metadata;
    data: StockData[];
};