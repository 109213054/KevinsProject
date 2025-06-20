from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# 替換 <db_password> 為你 TSMCProject 資料庫使用者的密碼
uri = "mongodb+srv://TSMCProject:Tyi9kDm6ZKOUgC4s@kevindb.opz402v.mongodb.net/?retryWrites=true&w=majority&appName=KevinDB"

client = MongoClient(uri, server_api=ServerApi('1'))

try:
    client.admin.command('ping')
    print("✅ 成功連線到 MongoDB Atlas！")
except Exception as e:
    print("❌ 連線失敗，錯誤訊息：", e)