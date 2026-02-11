from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
import uvicorn
import os
import threading
import datetime

# 引入核心邏輯
import main 
from src import config

# === 設定全域變數 ===
OUTPUT_DIR = config.OUTPUT_DIR
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def run_screener_task():
    """執行選股邏輯的包裝函式"""
    print(f"[{datetime.datetime.now()}] ⏰ 排程啟動：開始執行選股策略...")
    try:
        main.main()
        print(f"[{datetime.datetime.now()}] ✅ 排程完成：數據已更新")
    except Exception as e:
        print(f"❌ 執行失敗: {e}")

# === 定義生命週期 (Lifespan) ===
# 這裡控制 Server 啟動和關閉時要做的事
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. 啟動排程器
    scheduler = BackgroundScheduler()
    # 設定每天下午 15:00 (台股收盤後) 自動執行
    # timezone 請根據 Zeabur 伺服器設定，通常設定 'Asia/Taipei'
    scheduler.add_job(run_screener_task, 'cron', hour=20, minute=0, timezone='Asia/Taipei')
    scheduler.start()
    print("📅 排程器已啟動：每天 15:00 自動更新")

    # 2. 啟動時檢查有沒有資料，沒有就先跑一次 (避免前端 404)
    json_path = os.path.join(OUTPUT_DIR, "results.json")
    if not os.path.exists(json_path):
        print("⚠️ 找不到 results.json，正在執行初始化選股...")
        # 使用執行緒跑，避免卡住啟動流程
        thread = threading.Thread(target=run_screener_task)
        thread.start()
    
    yield
    
    # 關閉時的動作
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

# === CORS 設定 ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 生產環境建議改成前端網址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === 路由設定 ===

# 1. 提供靜態檔案 (讓前端可以抓到 results.json)
app.mount("/data", StaticFiles(directory=OUTPUT_DIR), name="data")

# 2. 手動觸發 API
@app.post("/update")
def trigger_update():
    thread = threading.Thread(target=run_screener_task)
    thread.start()
    return {"status": "Update started", "message": "Backend is updating data in background..."}

@app.get("/")
def read_root():
    return {
        "status": "ok", 
        "service": "Minervini Screener API",
        "last_update": "Check /data/results.json metadata"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)