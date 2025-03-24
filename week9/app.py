from fastapi import FastAPI, Request
from fastapi.responses import FileResponse ,JSONResponse
from typing import Optional
import json
import mysql.connector # 與 MySQL 資料庫建立連線
import os # 操作檔案系統，如 os.path.dirname(__file__) 取得目前檔案所在的目錄
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 建立 FastAPI 應用程式，這將是我們的 API 伺服器
app=FastAPI()
#####################################################################
# 設置 CORS 允許來自特定來源的請求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允許來自這個 URL 的請求
    allow_credentials=True,
    allow_methods=["*"],  # 允許所有 HTTP 方法
    allow_headers=["*"],  # 允許所有標頭
)

# 偵測我目前執行資料夾的位置
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
print("目前資料夾位置:",STATIC_DIR)

# Static Pages (Never Modify Code in this Block)
@app.get("/", include_in_schema=False)
async def index(request: Request):
	return FileResponse("./static/index.html", media_type="text/html")
@app.get("/attraction/{id}", include_in_schema=False)
async def attraction(request: Request, id: int):
	return FileResponse("./static/attraction.html", media_type="text/html")
@app.get("/booking", include_in_schema=False)
async def booking(request: Request):
	return FileResponse("./static/booking.html", media_type="text/html")
@app.get("/thankyou", include_in_schema=False)
async def thankyou(request: Request):
	return FileResponse("./static/thankyou.html", media_type="text/html")
# include_in_schema=False 代表這些路由 不會顯示在 API 文件（例如 Swagger UI）

# Week9
# 開啟並讀取 taipei-attractions.json 檔案
with open("data/taipei-attractions.json", "r", encoding="utf-8") as file:
    data = json.load(file) # 將 JSON 轉換成 Python 字典 (dict)

# 從 JSON 中提取景點資料：景點資料是一個 列表 (list)
attractions = data["result"]["results"]

# 定義 mrt_stations（假設從 attractions 取得資料）
mrt_stations = []
for attraction in attractions:
    mrt = attraction.get("MRT", "")
    if mrt:
        station = next((s for s in mrt_stations if s["name"] == mrt), None)
        if not station:
            mrt_stations.append({"name": mrt, "attractions_count": 1})
        else:
            station["attractions_count"] += 1

# 3個API
@app.get("/api/attractions")
async def get_attractions(page: int = 0, keyword: Optional[str] = None):
    print(f"API 被呼叫: /api/attractions?page={page}&keyword={keyword}")  # Debug 訊息
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="0000",
        database="taipei_day_trip",
        charset="utf8mb4"  # 確保 MySQL 連線使用 UTF-8

    )
    cursor = conn.cursor(dictionary=True)

    limit = 12
    offset = page * limit 

    sql = "SELECT id, name, category, description, address, transport, mrt, latitude, longitude, images FROM attractions"
    
    params = []
    if keyword:
        sql += " WHERE name LIKE %s OR mrt LIKE %s"
        search_keyword = f"%{keyword}%"
        params.extend([search_keyword, search_keyword])

    sql += " LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    cursor.execute(sql, params)
    results = cursor.fetchall()

    # if keyword:
    #     sql += " WHERE name LIKE %s OR mrt LIKE %s"
    #     search_keyword = f"%{keyword}%"
    #     cursor.execute(sql + " LIMIT %s OFFSET %s", (search_keyword, search_keyword, limit, offset))
    # else:
    #     cursor.execute(sql + " LIMIT %s OFFSET %s", (limit, offset))

    # results = cursor.fetchall()

    for attraction in results:
        attraction["images"] = json.loads(attraction["images"])  

    # 計算總數
    count_sql = "SELECT COUNT(*) FROM attractions"
    count_params = []
    if keyword:
        count_sql += " WHERE name LIKE %s OR mrt LIKE %s"
        count_params.extend([search_keyword, search_keyword])
    cursor.execute(count_sql, count_params)
    
    total_count = cursor.fetchone()["COUNT(*)"]
    next_page = page + 1 if total_count > (offset + limit) else None


    # # 重新計算 total_count (根據 keyword 來查詢總數)
    # if keyword:
    #     cursor.execute("SELECT COUNT(*) FROM attractions WHERE name LIKE %s OR mrt LIKE %s", (search_keyword, search_keyword))
    # else:
    #     cursor.execute("SELECT COUNT(*) FROM attractions")

    # total_count = cursor.fetchone()["COUNT(*)"]

    # # 只有當有查詢結果時才決定 nextPage
    # next_page = page + 1 if total_count > (offset + limit) and results else None

    cursor.close()
    conn.close()

    return JSONResponse({"nextPage": next_page, "data": results}, media_type="application/json; charset=utf-8")

@app.get("/api/attraction/{attractionId}")
async def get_attraction(attractionId: int):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="0000",
        database="taipei_day_trip",
        charset="utf8mb4"  # 確保 MySQL 連線使用 UTF-8

    )
    cursor = conn.cursor(dictionary=True)

    # 查詢指定景點
    sql = "SELECT id, name, category, description, address, transport, mrt, latitude, longitude, images FROM attractions WHERE id = %s"
    cursor.execute(sql, (attractionId,))
    attraction = cursor.fetchone()

    # 如果找不到景點，回傳 404
    if not attraction:
        cursor.close()
        conn.close()
        return JSONResponse({"error":True,"message":"景點編號不正確"},status_code=404)

    # 確保 `images` 是乾淨的 list
    attraction["images"] = json.loads(attraction["images"])

    # 關閉連線
    cursor.close()
    conn.close()

    return JSONResponse({"data": attraction})

    # 400-499: Client Error
    # 500-599: Server Error
    # 200-299: Success
    # 300-399: Redirect 跳轉
    # 100-199: Informational 資訊

@app.get("/api/mrts")
async def get_mrts():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="0000",
        database="taipei_day_trip",
        charset="utf8mb4"  # 確保 MySQL 連線使用 UTF-8

    )
    cursor = conn.cursor(dictionary=True)

    # 從 MySQL 查詢各 MRT 站的景點數量
    sql = """
    SELECT mrt, COUNT(*) as attractions_count 
    FROM attractions 
    WHERE mrt IS NOT NULL AND mrt != ''
    GROUP BY mrt 
    ORDER BY attractions_count DESC;
    """
    cursor.execute(sql)
    mrt_stations = cursor.fetchall()

    # 關閉連線
    cursor.close()
    conn.close()

    # 只回傳捷運站名稱（依景點數排序）
    return JSONResponse({"data": [mrt["mrt"] for mrt in mrt_stations]})  # 只回傳捷運站名稱

# 掛載靜態資源
app.mount("/static", StaticFiles(directory="static"), name="static")

# taskkill /F /IM python.exe /T
