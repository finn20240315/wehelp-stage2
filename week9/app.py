# app 是 view response 是 view
import jwt,datetime, json, httpx, uuid, os
from fastapi import FastAPI, Request,HTTPException
# FastAPI：主要的 Web 框架，負責建立 API 伺服器
# Request：用來處理 HTTP 請求，獲取請求相關資訊
from fastapi.responses import FileResponse ,JSONResponse
# FileResponse：用來回傳靜態 HTML 檔案，例如首頁或其他網頁
# JSONResponse：回傳 JSON 格式的資料，適用於 API
from typing import Optional #Optional：用來定義參數為可選（非必填）。例如：Optional[str] 代表參數可以是字串或是 None
import json # 處理 JSON 格式的資料
import mysql.connector # 與 MySQL 資料庫建立連線，查詢景點資訊
from mysql.connector import pooling
import os # 操作檔案系統，如 os.path.dirname(__file__) 取得目前檔案所在的目錄
from fastapi.middleware.cors import CORSMiddleware # 解決 CORS（跨來源請求） 問題，允許前端從不同網域存取 API
from fastapi.staticfiles import StaticFiles #
import jwt
import datetime
import json
import httpx
import uuid
from dotenv import load_dotenv
from db import connPool
from routers import booking

load_dotenv() # 讀取 .env 檔

# === JWT 設定 ===
JWT_SECRET =os.getenv("JWT_SECRET")

# 建立 FastAPI 應用程式，這將是我們的 API 伺服器
app=FastAPI()

app.include_router(booking.router) # 將 booking 路由器掛載到 FastAPI 應用程式上

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


# 3個API
@app.get("/api/attractions")
async def get_attractions(page: int = 0, keyword: Optional[str] = None):
    print(f"API 被呼叫: /api/attractions?page={page}&keyword={keyword}")  # Debug 訊息
    
    conn = connPool.get_connection()
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
    conn = connPool.get_connection()
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
    conn = connPool.get_connection()
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

# Week12
# 註冊一個新的會員
@app.post("/api/user")
async def signup(request:Request):
    try:
        body=await request.json()
        print(body)  # 調試訊息
        name=body.get("name")
        email=body.get("email")
        password=body.get("password")

        conn = connPool.get_connection()
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

        conn = connPool.get_connection()
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

# Week13




# 整體流程：
# 使用者在 /booking 頁看到信用卡輸入欄位
# 點擊「確認訂購並付款」→ 取得 TapPay Prime
# 將 Prime 與訂單資料送到後端 /api/orders
# 後端建立 UNPAID 訂單 → 發送付款請求給 TapPay
# 根據付款結果：
#      成功 → 將訂單標記為 PAID，回傳 order number
#      失敗 → 保持 UNPAID，仍回傳 order number
# 前端接收 order number → 導向 /thankyou?number=xxx
# /thankyou 頁讀取參數 → 顯示訂單號碼

# 前端 booking.js
# /booking	建立付款按鈕，發送訂單資料與 Prime 給後端
# /thankyou 從網址取得 order number，顯示訂單成功畫面

# 後端 app.py
# 後端收到前端送來的 Prime 與訂單資訊
# 建立訂單（order）	存入資料庫，產生訂單編號
# 呼叫 TapPay API	用 Prime 發送付款請求
# 儲存付款紀錄	成功 → 訂單設為 PAID，失敗 → 留 UNPAID
# 回傳 JSON	包含 order_number

# week14
# 建立 order API
@app.post("/api/order")
async def post_order(request:Request):
    body = await request.json()
    print("前端傳來的資料：", body)
   
    order_number=str(uuid.uuid4())[:20]

    # 發送 httpx 請求給 TapPay pay by prime api
    async with httpx.AsyncClient()as client:
        response=await client.post("https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime",
            headers= {"Content-Type": "application/json",
                      "x-api-key": os.getenv("PARTNER_KEY")},
            json={
            "prime": body["prime"],
            "partner_key": os.getenv("PARTNER_KEY"),
            "merchant_id": os.getenv("MERCHANT_ID"), 
            "amount": body["order"]["price"],
            "currency":"TWD",
            "order_number":order_number,
            "details":"TapPay Test",
            "cardholder": {
                "phone_number": body["order"]["contact"]["phone"],
                "name": body["order"]["contact"]["name"],
                "email": body["order"]["contact"]["email"],
                },
            "remember": True
            }
        )
        
        result=response.json()
        print(response.status_code)  # 200
        print("從tappay api收到的回傳資料：",result)
        
    
    if result["status"]==0:
        print("交易成功！")
    else:
        return JSONResponse(content={"error": True, "message": "付款失敗"}, status_code=400)

    conn = connPool.get_connection()
    cursor = conn.cursor(dictionary=True)

    try:       
        token = request.headers.get("Authorization").split(" ")[1]  # 取得 Bearer Token
        payload = jwt.decode(token,JWT_SECRET,algorithms="HS256")
        user_id=payload["data"]["id"]
        print("TOKEN 是  ：",token)
        print("USER_ID 是 ：",user_id)
    except Exception as e:
        return JSONResponse(content={"error":True,"message":"無效的使用者驗證"},status_code=401)

    # 新增 member 表 phone 欄位
    # 查詢欄位是否已存在
    cursor.execute("SHOW COLUMNS FROM member LIKE 'phone'")
    phone_result = cursor.fetchone()

    if phone_result:
        print("欄位 'phone' 已存在，不需新增。")
    else:
        try:
            cursor.execute("ALTER TABLE member ADD COLUMN phone VARCHAR(20)")
            print("成功新增欄位 'phone'")
        except mysql.connector.Error as err:
            print("新增欄位失敗：", err)

    # 新增資料到 member 表 
    cursor.execute("UPDATE member SET phone = %s WHERE id = %s", (body["order"]["contact"]["phone"],user_id))
    conn.commit()

    status = None
    if result["status"] == 0:
        status="PAID"
    else:
        status="UNPAID"

    # 新增訂單資料到 order 表
    cursor.execute("""
                   INSERT INTO orders(
                   user_id,attraction_id,date,time,price,
                   order_number,status,rec_trade_id
                   ) VALUES (%s, %s, %s,%s, %s, %s,%s, %s)""",
                    (user_id,
                     body["order"]["trip"]["attraction"]["id"],
                     body["order"]["trip"]["date"], 
                     body["order"]["trip"]["time"],
                     body["order"]["price"],
                     result["order_number"],
                     status,
                     result["rec_trade_id"]
                     ))
    conn.commit()


    cursor.execute("DELETE FROM booking WHERE user_id = %s", (user_id,))
    conn.commit()
    conn.close()

    return JSONResponse(content={"ok":True,"order_number": order_number,"message": "付款成功"}, status_code=200)
    
@app.get("/api/order/{orderNumber}")
async def get_order(request:Request,orderNumber):

    conn = connPool.get_connection()
    cursor = conn.cursor(dictionary=True)
     
    cursor.execute("SELECT * FROM orders WHERE order_number = %s", (orderNumber,))
    order = cursor.fetchone()
    
    cursor.close()
    conn.close()

    if not order:
        return JSONResponse(status_code=404,content={"error":"找不到訂單"})
    
    return {
            "data": {
                "number": order["order_number"],
                "price": order["price"],
                "status": order["status"],
                "attraction": {
                    "id": order["attraction_id"],
                    "name": order["attraction_name"],
                    "address": order["attraction_address"],
                    "image": order["attraction_image"]
                },
                "date": order["date"],
                "time": order["time"],
                "contact": {
                    "name": order["contact_name"],
                    "email": order["contact_email"],
                    "phone": order["contact_phone"]
                }
            }
        }

# 掛載靜態資源
app.mount("/static", StaticFiles(directory="static"), name="static")

# taskkill /F /IM python.exe /T
