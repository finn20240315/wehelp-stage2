from fastapi import *
from fastapi.responses import FileResponse
from typing import List, Optional
import json
import mysql.connector
import os
import re

app=FastAPI()

# 設定靜態檔案夾的位置
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

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

# Week9
# 讀取 JSON 檔案
with open(r"C:\Users\shiyi\Others\Program\Wehelp_6th_beggin_20250106\taipei-day-trip\taipei-day-trip\data\taipei-attractions.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# 解析數據
attractions = data["result"]["results"]

# 連線到 MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="0000",
    database="taipei_day_trip"
)
cursor = conn.cursor()

# 建立資料表（如果不存在）
cursor.execute("""
CREATE TABLE IF NOT EXISTS attractions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(255),
    description TEXT,
    address VARCHAR(255),
    transport TEXT,
    mrt VARCHAR(255),
    latitude FLOAT,
    longitude FLOAT,
    images TEXT
);
""")

# 過濾符合條件的圖片
def filter_images(image_urls):
    pattern = re.compile(r"https?://.*\.(jpg|jpeg|png)$", re.IGNORECASE)
    valid_images = [url.strip() for url in image_urls.split("https://") if pattern.match("https://" + url)]
    return json.dumps(["https://" + url for url in valid_images])

# 插入景點資料
for attraction in attractions:
    name = attraction["name"]
    category = attraction.get("CAT", "")
    description = attraction.get("description", "")
    address = attraction.get("address", "")
    transport = attraction.get("direction", "")
    mrt = attraction.get("MRT", "")
    latitude = float(attraction["latitude"])
    longitude = float(attraction["longitude"])
    images = filter_images(attraction["file"])

    sql = """
    INSERT INTO attractions (name, category, description, address, transport, mrt, latitude, longitude, images)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (name, category, description, address, transport, mrt, latitude, longitude, images))

# 提交變更並關閉連線
conn.commit()

print("資料已成功存入 MySQL！")

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
    # 篩選資料
    filtered_attractions = [attr for attr in attractions if (not keyword or keyword.lower() in attr["name"].lower() or (attr.get("mrt") and keyword.lower() in attr.get("mrt", "").lower()))]
    # 分頁邏輯
    start = page * 12
    end = start + 12
    data = filtered_attractions[start:end]
    
    # 回應資料
    next_page = page + 1 if len(filtered_attractions) > end else None
    
    return {"nextPage": next_page, "data": data}

@app.get("/api/attraction/{attractionId}")
async def get_attraction(attractionId: int):
    print("印出景點data：",attractions)  # 打印 attractions 檢查結構
	# 查找景點資料
    attraction = next((attr for attr in attractions if attr["id"] == attractionId), None)
    
    if not attraction:
        raise HTTPException(status_code=404, detail="景點編號不正確")
    
    return {"data": attraction}

@app.get("/api/mrts")
async def get_mrts():
    # 根據景點數量排序
    mrt_stations_sorted = sorted(mrt_stations, key=lambda x: x["attractions_count"], reverse=True)
    
    # 回傳捷運站名稱
    return {"data": [mrt["name"] for mrt in mrt_stations_sorted]}

# print("前三筆資料：",attractions[:3])  # 打印前三筆資料檢查是否有 'id'

# 查詢資料庫並檢查資料
cursor.execute("SELECT * FROM attractions")
columns = [column[0] for column in cursor.description]  # 取得欄位名稱
attractions = [dict(zip(columns, row)) for row in cursor.fetchall()]

cursor.close()
conn.close()

# taskkill /F /IM python.exe /T
