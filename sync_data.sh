#!/bin/bash

# 1. 進入 backend 資料夾執行 Python
echo "Running Backend..."
cd backend
python main.py

# 2. 回到上一層 (根目錄)
cd ..

# 3. 確保前端目標資料夾存在 (防呆)
mkdir -p frontend/public

# 4. 複製檔案
echo "Syncing data to Frontend..."
cp backend/output/results.json frontend/public/

echo "Done! Data synced to frontend/public/results.json"