import json
import mysql.connector # 與 MySQL 資料庫建立連線
import os # 操作檔案系統，如 os.path.dirname(__file__) 取得目前檔案所在的目錄
import re # 正規表達式

# Week9
# 開啟並讀取 taipei-attractions.json 檔案
with open("data/taipei-attractions.json", "r", encoding="utf-8") as file:
    data = json.load(file) # 將 JSON 轉換成 Python 字典 (dict)

# 從 JSON 中提取景點資料：景點資料是一個 列表 (list)
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
    id INT PRIMARY KEY AUTO_INCREMENT, # 主鍵，自動遞增
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


