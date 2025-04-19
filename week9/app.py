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
from datetime import date
import json
import httpx
import uuid
# pip install re

# === JWT 設定 ===
JWT_SECRET = "my-secret-key"

# 建立 FastAPI 應用程式，這將是我們的 API 伺服器
app=FastAPI()

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

# Week13
# 建立預訂 API
@app.post("/api/booking")
async def post_booking(request:Request):
    body=await request.json() # request 是參數：前端用json格式傳來的資料，解析json()
    print(body)  # 調試訊息

    user_id=body.get("user_id") 
    attraction_id=body.get("attraction_id")
    date=body.get("date")
    time=body.get("time")
    price=body.get("price")  # 所以前端要 fetch 到一個json資料裡面要有這些資料對吧?

    conn=mysql.connector.connect( # connn 是什麼意思?
        host="localhost", # # 主機名稱，通常是 localhost
        user="root", # 使用者名稱，這邊是 root
        password="0000", # 密碼，這邊是 0000
        database="taipei_day_trip", # 資料庫名稱，這邊是 taipei_day_trip
        charset="utf8mb4"  # 確保 MySQL 連線使用 UTF-8
    )
    cursor=conn.cursor(dictionary=True) # 這句是什麼意思?
    
    token = request.headers.get("Authorization") # token 不是存在 localStorage 裡面嗎?
     # 我要怎麼看到 request 的資料? print(request) ?

    if token is None: # 如果 token 不存在，代表使用者沒有登入
    # 要改成 if not token 
        return JSONResponse({"error":True,"message":"請先登入會員"},status_code=401)
    # 直接把 login 葉面跳出來顯示
   
    try:
        token = token.split(" ")[1]  # 取得 Bearer Token
        
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("data").get("id") # 這裡是什麼意思?
        print(payload)

    except jwt.ExpiredSignatureError: # 這邊在說什麼?
         return JSONResponse({"error":True,"message":"Token 已過期"},status_code=401)

    except jwt.PyJWTError: # 這邊是什麼?
        return JSONResponse({"error":True,"message":"無效的 token"},status_code=401)
    
    sql = """
    INSERT INTO booking (user_id, attraction_id, date, time, price)
    VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute("DELETE FROM booking WHERE user_id = %s", (user_id,))

    cursor.execute(sql, (user_id, attraction_id, date, time, price))
    conn.commit()  # 提交交易，將資料寫入資料庫

    cursor.close()
    conn.close()

    print("Body JSON:", body); # 前端送的 JSON 資料
    print("Authorization Header:", token); # header 裡拿到的 token
    print("Decoded Token Payload:", payload); # 解開 token 得到的使用者資訊
    
    return JSONResponse({"ok":True,"message":"預訂成功"},status_code=200)
    



# 取得預定資料 API
@app.get("/api/booking")
def get_booking(request:Request):
    # 使用者一進入api就需驗證是否有在header夾帶token
    # 解析 token 取得 id 是什麼，然後進去 sql booking 撈資料 取得 date time price
    # 取得 attraction_id 再撈 attraction 資料 ，動態添加 name address image
    # 將撈到的資料，動態添加到 booking.html 上
    # (這是order api 的事)在同一個頁面 bookin.html 上，將 聯絡資訊 & 付款資訊也一併存入 sql 裡面 ，再創一個表?

    token=request.headers.get("Authorization")
    print("token",token)
    if token is None:
        return JSONResponse({"error":True,"message":"請先登入會員"},status_code=400)
    # 為什麼這裡用 jsonresponse token 又不是json 格式
    # 為什麼這裡是回傳 error:true，而不是回傳 ok:true ? 如果我寫成 if token is true，是不是就回傳 ok:true ?

    # 解析token
    try:
        print("token[0]",token.split(" ")[0])
        print("token[1]",token.split(" ")[1])

        token=token.split(" ")[1]
        payload=jwt.decode(token, JWT_SECRET,algorithms=["HS256"]) # 這邊是什麼意思?
        user_id=payload.get("data").get("id") # payload 長什麼樣子?
        print(payload)
    except jwt.ExpiredSignatureError: # 這兩個又沒有條件篩選，怎麼知道哪個是 token 過期，哪個是 token 無效?
        return JSONResponse({"error":True,"message":"token 已過期"},status_code=401)
    except jwt.PyJWTError:
        return JSONResponse({"error":True,"message":"無效的 token"},status_code=401)
    
    # 這邊是排除了 if token is none、並且嘗試 try (沒有2個 except)才會執行的地方對嗎?
    conn=mysql.connector.connect(
        host="localhost",
        username="root",
        password="0000",
        database="taipei_day_trip",
        charset="utf8mb4"
    )
    cursor=conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM booking WHERE user_id=%s",(user_id,))
    booking = cursor.fetchone()  # <-- 一定要讀出來，不能省
    # 對資料庫的變更才需要 conn.commit，例如 INSERT、UPDATE、DELETE
    print("booking 資料：", booking)

    if not booking:
        cursor.close()
        conn.close()
        return {"data":None}

   # 查 attraction 資料
    attraction_id = booking["attraction_id"]
    cursor.execute("SELECT id, name, address, images FROM attractions WHERE id=%s", (attraction_id,))
    attraction = cursor.fetchone()

    if not attraction:
        cursor.close()
        conn.close()
        return {"date":None}

    images=json.loads(attraction["images"])
    print("json.loads後的資料格式：",images)
    print(type(images))

    print("第一張圖片網址：",images[0])

    date_str=booking["date"].strftime("%Y-%m-%d")

    return JSONResponse({
        "data": {
            "attraction": {
                "id": attraction["id"],
                "name": attraction["name"],
                "address": attraction["address"],
                "images":images[0] 
            },
            "date": date_str,
            "time": booking["time"],
            "price": booking["price"]
        }
    },status_code=200)

@app.delete("/api/booking")
def delete_booking(request:Request):
    token=request.headers.get("Authorization")

    if token is None:
        return JSONResponse({"error":True,"message":"請先登入會員"},status_code=403)
   
    try:
        token=token.split(" ")[1]
        payload=jwt.decode(token, JWT_SECRET,algorithms=["HS256"]) # 這邊是什麼意思?
        user_id=payload.get("data").get("id") # payload 長什麼樣子?

    except jwt.ExpiredSignatureError: # 這兩個又沒有條件篩選，怎麼知道哪個是 token 過期，哪個是 token 無效?
        return JSONResponse({"error":True,"message":"token 已過期"},status_code=401)
    except jwt.PyJWTError:
        return JSONResponse({"error":True,"message":"無效的 token"},status_code=401)
    
    conn=mysql.connector.connect(
        host="localhost",
        username="root",
        password="0000",
        database="taipei_day_trip",
        charset="utf8mb4"
    )
    cursor=conn.cursor(dictionary=True)

    cursor.execute("DELETE FROM booking WHERE user_id=%s",(user_id,))
    conn.commit()

    cursor.close()
    conn.close()
    
    print("資料刪除成功")

    return JSONResponse({"ok":True,"message":"資料刪除成功"},status_code=200)

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
                      "x-api-key": "partner_5lGT3A0K7hnY9sqKvBy8hNwfvWoEQ3ISXgDJxoVGQj2IEeWJAOKawxkj"},
            json={
            "prime": body["prime"],
            "partner_key": "partner_5lGT3A0K7hnY9sqKvBy8hNwfvWoEQ3ISXgDJxoVGQj2IEeWJAOKawxkj",
            "merchant_id": "shiyingtong2022_CTBC", 
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

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="0000",
        database="taipei_day_trip",
        charset="utf8mb4"  # 確保 MySQL 連線使用 UTF-8
    )
    cursor = conn.cursor(dictionary=True)
           
    token = request.headers.get("Authorization").split(" ")[1]  # 取得 Bearer Token
    payload = jwt.decode(token,JWT_SECRET,algorithms="HS256")
    user_id=payload["data"]["id"]
    print("TOKEN 是  ：",token)
    print("USER_ID 是 ：",user_id)

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

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="0000",
        database="taipei_day_trip",
        charset="utf8mb4"  # 確保 MySQL 連線使用 UTF-8
    )
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
