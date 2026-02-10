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
}

export interface APIResponse {
    metadata: Metadata;
    data: StockData[];
}