from fastapi import *
from fastapi.responses import FileResponse ,JSONResponse
from typing import List, Optional
import json
import mysql.connector # 與 MySQL 資料庫建立連線
import os # 操作檔案系統，如 os.path.dirname(__file__) 取得目前檔案所在的目錄
import re # 正規表達式

# 建立 FastAPI 應用程式，這將是我們的 API 伺服器
app=FastAPI()

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
    # 連線到 MySQL
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="0000",
        database="taipei_day_trip"
    )
    cursor = conn.cursor(dictionary=True)

    # 計算要跳過的筆數
    limit = 12
    offset = page * limit 

    # 構造 SQL 查詢語句
    sql = "SELECT id, name, category, description, address, transport, mrt, latitude, longitude, images FROM attractions"
    
    # 如果有關鍵字，增加 WHERE 條件
    if keyword:
        sql += " WHERE name LIKE %s OR mrt LIKE %s"
        search_keyword = f"%{keyword}%"
        cursor.execute(sql + " LIMIT %s OFFSET %s", (search_keyword, search_keyword, limit, offset))
    else:
        cursor.execute(sql + " LIMIT %s OFFSET %s", (limit, offset))

    results = cursor.fetchall()

    # 確保 `images` 欄位是乾淨的 list
    for attraction in results:
        attraction["images"] = json.loads(attraction["images"])  # 轉換回 list

    # 計算是否還有下一頁
    cursor.execute("SELECT COUNT(*) FROM attractions")
    total_count = cursor.fetchone()["COUNT(*)"]
    next_page = page + 1 if total_count > offset + limit else None

    # 關閉資料庫連線
    cursor.close()
    conn.close()

    return JSONResponse({"nextPage": next_page, "data": results})

@app.get("/api/attraction/{attractionId}")
async def get_attraction(attractionId: int):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="0000",
        database="taipei_day_trip"
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
        database="taipei_day_trip"
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

# taskkill /F /IM python.exe /T
