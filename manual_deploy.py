import os
import glob
import subprocess
import sys
from datetime import datetime

# === 設定路徑 ===
ROOT_DIR = os.getcwd() # 預期在專案根目錄執行
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
CACHE_DIR = os.path.join(BACKEND_DIR, "cache")
OUTPUT_FILE = os.path.join(BACKEND_DIR, "output", "results.json")
MAIN_SCRIPT = os.path.join(BACKEND_DIR, "main.py")

def step_1_clean_cache():
    """清理 backend/cache 下的所有 .pkl 檔案"""
    print("\n[Step 1] 🧹 正在清理舊快取...")
    
    if not os.path.exists(CACHE_DIR):
        print("   快取目錄不存在，跳過。")
        return

    # 搜尋所有 .pkl 檔案
    files = glob.glob(os.path.join(CACHE_DIR, "*.pkl"))
    if not files:
        print("   沒有發現舊快取。")
    
    for f in files:
        try:
            os.remove(f)
            print(f"   已刪除: {os.path.basename(f)}")
        except Exception as e:
            print(f"   刪除失敗 {f}: {e}")

def step_2_run_screener():
    """執行 backend/main.py"""
    print("\n[Step 2] 🚀 正在執行選股程式 (這需要幾分鐘，請耐心等待)...")
    
    # 使用當前環境的 python 執行
    # cwd=ROOT_DIR 確保相對路徑正確
    try:
        result = subprocess.run(
            [sys.executable, "backend/main.py"], 
            cwd=ROOT_DIR,
            check=True # 如果回傳非 0 (報錯) 會直接拋出異常
        )
    except subprocess.CalledProcessError:
        print("❌ 後端執行發生錯誤！停止部署。")
        sys.exit(1)

def step_3_git_push():
    """強制將 results.json 推送到 GitHub"""
    print("\n[Step 3] 📦 正在上傳數據到 GitHub...")

    if not os.path.exists(OUTPUT_FILE):
        print(f"❌ 找不到輸出檔案: {OUTPUT_FILE}，無法上傳。")
        sys.exit(1)

    try:
        # 1. 強制加入 git (因為它通常被 .gitignore 忽略)
        print("   執行 git add -f...")
        subprocess.run(["git", "add", "-f", "backend/output/results.json"], check=True)

        # 2. 提交變更
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        commit_msg = f"Data Update: Manual run at {timestamp}"
        print(f"   執行 git commit ({commit_msg})...")
        
        # check=False 因為如果檔案沒變，commit 會回傳 1 (這不是錯誤)
        subprocess.run(["git", "commit", "-m", commit_msg], check=False)

        # 3. 推送到遠端
        print("   執行 git push...")
        subprocess.run(["git", "push"], check=True)
        
        print("\n✅ 成功！數據已推送到 GitHub。")
        print("   Zeabur 將會偵測到 commit 並自動重新部署 (約需 1-2 分鐘)。")

    except subprocess.CalledProcessError as e:
        print(f"❌ Git 操作失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=== Minervini 手動部署工具 ===")
    print("此工具將會：清理快取 -> 重跑爬蟲 -> 強制上傳 JSON 到 GitHub")
    
    step_1_clean_cache()
    step_2_run_screener()
    step_3_git_push()