from fastapi import FastAPI, Request,HTTPException,Depends
# FastAPI：主要的 Web 框架，負責建立 API 伺服器
# Request：用來處理 HTTP 請求，獲取請求相關資訊
from fastapi.responses import FileResponse ,JSONResponse
# FileResponse：用來回傳靜態 HTML 檔案，例如首頁或其他網頁
# JSONResponse：回傳 JSON 格式的資料，適用於 API
from typing import Optional #Optional：用來定義參數為可選（非必填）。例如：Optional[str] 代表參數可以是字串或是 None
import json # 處理 JSON 格式的資料
import mysql.connector # 與 MySQL 資料庫建立連線，查詢景點資訊
import os # 操作檔案系統，如 os.path.dirname(__file__) 取得目前檔案所在的目錄
from fastapi.middleware.cors import CORSMiddleware # 解決 CORS（跨來源請求） 問題，允許前端從不同網域存取 API
from fastapi.staticfiles import StaticFiles #
import jwt
import datetime

# === JWT 設定 ===
JWT_SECRET = "my-secret-key"

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

#     1. 前端提供輸入框，讓使用者輸入會員帳號密碼
#     2. 將前端樹入的資料傳到後端，存到資料庫
#     3. 當使用者要登入時，去資料庫撈資料看是否吻合
#     4. 如果吻合就讓使用者登入
#     5. 之後在使用者瀏覽網站的每個畫面都保持登入，直到過了使用期限或者使用者自己登出

# 註冊一個新的會員
@app.post("/api/user")
async def signup(request:Request):
    try:
        body=await request.json()
        print(body)  # 調試訊息
        name=body.get("name")
        email=body.get("email")
        password=body.get("password")

        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="0000",
            database="taipei_day_trip",
            charset="utf8mb4"  # 確保 MySQL 連線使用 UTF-8
        )
        cursor = conn.cursor(dictionary=True)
        
        # 檢查帳號是否已存在
        cursor.execute("SELECT email FROM member WHERE email = %s", (email,))
        if cursor.fetchone():
            return JSONResponse(content={"error":True,"message": "使用者信箱已被註冊"}, status_code=400)
                
        # 新增使用者
        cursor.execute("INSERT INTO member(username,email, password) VALUES (%s, %s, %s)", (name, email, password))
        conn.commit()
        
        return JSONResponse(content={"ok":True,"message": "註冊成功"}, status_code=200)
    
    except Exception as e:
        print(f"註冊錯誤: {e}")  # 調試訊息
        return JSONResponse(content={"error":str(e)},status_code=500)
    
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# 取得當前登入的會員資訊
@app.get("/api/user/auth")
async def get_current_user(request: Request):
    conn=None
    cursor=None
    try:
        token = request.headers.get("Authorization").split(" ")[1]  # 取得 Bearer Token
        if token is None:
            return JSONResponse({"data":None},status_code=401)
        
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        id = payload.get("id")
        name = payload.get("name")
        email = payload.get("email")

        return {"data": {"id": id, "name": name, "email": email}}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已過期")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="無效的 token")
    finally:
        if cursor:cursor.close()
        if conn:conn.close()

# 登入會員帳戶
@app.put("/api/user/auth")
async def signin(request:Request):
    try:
        body = await request.json()  # 解析 JSON
        print(data)  # 調試訊息

        email=body.get("email")
        password=body.get("password")

        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="0000",
            database="taipei_day_trip",
            charset="utf8mb4"  # 確保 MySQL 連線使用 UTF-8
        )
        cursor = conn.cursor(dictionary=True)
        
        # 驗證帳號密碼
        cursor.execute("SELECT id,username, email,password FROM member WHERE email=%s AND password=%s", (email,password))
        user = cursor.fetchone()
        print("user:",user)  # 調試訊息

        if user is None:
            return JSONResponse({"error":True, "message": "帳號或密碼錯誤"}, status_code=400)
        
        payload={
            "data":{
                "id" : user["id"],
                "name":user["username"],
                "email":user["email"],
            },
            "exp":datetime.datetime.now()+datetime.timedelta(days=7) # 7天後過期
        }
        token = jwt.encode(payload,JWT_SECRET,algorithm="HS256")

        return JSONResponse({"token":token},status_code=200)
    
    except Exception as e:
        print(f"登入錯誤: {e}")  # 調試訊息
        return JSONResponse(content={"error":str(e)},status_code=500)
    
    finally:
        if cursor : cursor.close()
        if conn : conn.close()

# 掛載靜態資源
app.mount("/static", StaticFiles(directory="static"), name="static")

# taskkill /F /IM python.exe /T
