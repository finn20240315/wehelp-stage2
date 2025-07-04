# router 是 controllor

# 可以重複使用的東西才做封裝(=class、=切出來)
import os
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from fastapi import * 
from db import connPool
import jwt,json
from fastapi import APIRouter

router=APIRouter()

JWT_SECRET =os.getenv("JWT_SECRET")

class Booking():
    def __init__(self): # 這裡的 body 是從前端傳來的資料
        pass

    @classmethod
    def checkToken(cls, request): 
        token = request.headers.get("Authorization") 

        if token is None: 
            return JSONResponse({"error":True,"message":"根本沒有 token"},status_code=403)   

        return token.split(" ")[1] 


# 建立預訂 API
@router.post("/api/booking")
async def post_booking(request:Request):
    body=await request.json() 
    user_id=body.get("user_id") 
    attraction_id=body.get("attraction_id")
    date=body.get("date")
    time=body.get("time")
    price=body.get("price") 

    try:
        conn = connPool.get_connection()
        cursor=conn.cursor(dictionary=True) 
    
        token=Booking.checkToken(request)   
        print("token等於:",token)      

        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("data").get("id") 

    except jwt.ExpiredSignatureError: 
        return JSONResponse({"error":True,"message":"Token 已過期"},status_code=401)
   
    except jwt.PyJWTError: 
        return JSONResponse({"error":True,"message":"無效的 token"},status_code=401)
    
    sql = """
    INSERT INTO booking (user_id, attraction_id, date, time, price)
    VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute("DELETE FROM booking WHERE user_id = %s", (user_id,))

    cursor.execute(sql, (user_id, attraction_id, date, time, price))
    conn.commit()

    cursor.close()
    conn.close()

    return JSONResponse({"ok":True,"message":"預訂成功"},status_code=200)


@router.get("/api/booking")
async def get_booking(request:Request):
    try:
        conn = connPool.get_connection()
        cursor=conn.cursor(dictionary=True)

        token=Booking.checkToken(request)   

        payload=jwt.decode(token, JWT_SECRET,algorithms=["HS256"]) 
        user_id=payload.get("data").get("id") 
        
        cursor.execute("SELECT * FROM booking WHERE user_id=%s",(user_id,))
        booking = cursor.fetchone()
        
        if not booking:
            return {"data":None}
        
        attraction_id = booking["attraction_id"]
        cursor.execute("SELECT id, name, address, images FROM attractions WHERE id=%s", (attraction_id,))
        attraction = cursor.fetchone()

        if not attraction:
            return {"date":None}
        
        images=json.loads(attraction["images"])

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
    
    except jwt.ExpiredSignatureError:
        return JSONResponse({"error":True,"message":"token 已過期"},status_code=401)
    
    except jwt.PyJWTError:
        return JSONResponse({"error":True,"message":"無效的 token"},status_code=401)
    
    except Exception as e:
        return JSONResponse({"error": True, "message": f"伺服器錯誤：{str(e)}"}, status_code=500)

    finally:
        conn.close()
        cursor.close()



@router.delete("/api/booking")
async def delete_booking(request:Request):
    try:
        conn = connPool.get_connection()
        cursor=conn.cursor(dictionary=True)

        token=Booking.checkToken(request)
          
        payload=jwt.decode(token, JWT_SECRET,algorithms=["HS256"]) 
        user_id=payload.get("data").get("id") 

        cursor.execute("DELETE FROM booking WHERE user_id=%s",(user_id,))
        conn.commit()

        return JSONResponse({"ok":True,"message":"資料刪除成功"},status_code=200)

    except jwt.ExpiredSignatureError: 
        return JSONResponse({"error":True,"message":"token 已過期"},status_code=401)
    
    except jwt.PyJWTError:
        return JSONResponse({"error":True,"message":"無效的 token"},status_code=401)
    
    finally:
        cursor.close()
        conn.close()
        

