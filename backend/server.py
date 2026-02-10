from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import threading

# 引入原本的主程式邏輯
import main 
from src import config

app = FastAPI()

# 允許跨域請求 (讓前端可以抓到資料)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生產環境建議改成前端的網址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 設定輸出目錄
OUTPUT_DIR = config.OUTPUT_DIR
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# 1. 提供靜態檔案 (讓 /results.json 可以被下載)
app.mount("/data", StaticFiles(directory=OUTPUT_DIR), name="data")

# 2. 提供一個 API 觸發更新 (可選)
@app.post("/update")
def trigger_update():
    # 在背景執行爬蟲，避免卡住 Server
    thread = threading.Thread(target=main.main)
    thread.start()
    return {"status": "Update started", "message": "Backend is updating data..."}

# 3. 根目錄檢查
@app.get("/")
def read_root():
    return {"status": "ok", "service": "Minervini Screener API"}

if __name__ == "__main__":
    # 啟動時先跑一次爬蟲 (選用)
    # main.main() 
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))