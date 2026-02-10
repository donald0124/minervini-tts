import os

# === 系統路徑設定 ===
# 獲取當前檔案 (src/config.py) 的上一層目錄作為 BASE_DIR (即 backend/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# 確保目錄存在
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === 篩選門檻設定 (參照 PRD FR-04, FR-06) ===
RS_THRESHOLD = 70               # 相對強度需大於 70 (前 30%)
MIN_AVG_VOLUME_SHARES = 300000  # 最小 20日均量 (300張)
IPO_MIN_DAYS = 250              # 最小上市天數 (排除新股)

# === 技術型態參數 (參照 PRD FR-04) ===
DIST_FROM_LOW_THRESHOLD = 1.30  # 需高於 52週低點 30%
DIST_FROM_HIGH_THRESHOLD = 0.75 # 需在 52週最高點 25% 範圍內 (1 - 0.25)
MA_SLOPE_LOOKBACK = 22          # 判斷 200MA 斜率的回看天數 (約1個月)

# === 系統效能 ===
MAX_WORKERS = 16                # 資料下載並發執行緒數量