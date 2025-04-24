import json
import mysql.connector # 與 MySQL 資料庫建立連線
import os # 操作檔案系統，如 os.path.dirname(__file__) 取得目前檔案所在的目錄
import re # 正規表達式

# Week9
# 開啟並讀取本機的 taipei-attractions.json 檔案
with open("data/taipei-attractions.json", "r", encoding="utf-8") as file:
    data = json.load(file) # 將 JSON 轉換成 Python 字典 (dict)

# 從 JSON 中提取景點資料：景點資料是一個 列表 (list)
attractions = data["result"]["results"]

# 連線到 MySQL
conn = mysql.connector.connect(
    host="localhost",
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database="taipei_day_trip",
    charset="utf8mb4"  # 確保 MySQL 連線使用 UTF-8
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

# 先檢查 attractions 資料表是否有資料
cursor.execute("SELECT COUNT(*) FROM attractions")
count = cursor.fetchone()[0]  # 取得資料筆數

# 如果資料表內已有資料，就不執行 INSERT
if count == 0:
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

    conn.commit()
    print("資料已成功存入 MySQL！")
else:
    print("資料表已經有資料，不執行插入。")

# 創建 member 資料表
cursor.execute("""
CREATE TABLE IF NOT EXISTS member(
               id INT PRIMARY KEY AUTO_INCREMENT,
               username VARCHAR(255) NOT NULL, 
               email VARCHAR(255) NOT NULL UNIQUE,
               password VARCHAR(255) NOT NULL,
               time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
               );
""")
# UNIQUE 確保資料不能重複

conn.commit()
print("資料表 member 建立成功！")


# 創建 booking 資料表
cursor.execute("""
CREATE TABLE IF NOT EXISTS booking( 
               id INT PRIMARY KEY AUTO_INCREMENT,
               user_id INT NOT NULL, -- 對應到 member.id
               attraction_id INT NOT NULL, -- 對應到 attractions.id
               date DATE NOT NULL, -- 預定要去的日期
               time VARCHAR(255) NOT NULL, -- 預定時段：上半天或下半天
               price INT NOT NULL, -- 價格
               created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 訂單建立時間
               FOREIGN KEY (user_id) REFERENCES member(id), -- 外鍵，對應到 member 資料表的 id
               FOREIGN KEY (attraction_id) REFERENCES attractions(id) -- 外鍵，對應到 attractions 資料表的 id
               );
""")
conn.commit()
print("資料表 booking 建立成功！")

# 創建 order 資料表
cursor.execute("""
CREATE TABLE IF NOT EXISTS orders( 
               id INT PRIMARY KEY AUTO_INCREMENT,
               user_id INT NOT NULL, -- 對應到 member.id
               attraction_id INT NOT NULL, -- 對應到 attractions.id
               date DATE NOT NULL, -- 預定要去的日期
               time VARCHAR(255) NOT NULL, -- 預定時段：上半天或下半天
               price INT NOT NULL, -- 價格
               order_number VARCHAR(255) NOT NULL,
               status VARCHAR(255) DEFAULT "UNPAID",
               rec_trade_id VARCHAR(100),                  -- TapPay 交易編號
               created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 訂單建立時間
               
               FOREIGN KEY (user_id) REFERENCES member(id), -- 外鍵，對應到 member 資料表的 id
               FOREIGN KEY (attraction_id) REFERENCES attractions(id) -- 外鍵，對應到 attractions 資料表的 id
               );
""")
conn.commit()
print("資料表 order 建立成功！")

cursor.close()
conn.close()

print("資料庫已關閉離線！")