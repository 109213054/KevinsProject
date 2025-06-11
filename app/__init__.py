from flask import Flask, request
from flask_cors import CORS
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

mongo_client = None

def create_app():
    app = Flask(__name__)
    CORS(app)

    # 連線 MongoDB
    global mongo_client
    mongo_client = MongoClient(os.getenv("MONGO_URI"))

    @app.before_request
    def detect_ip_source():
        #X-Forwarded-For 會由 ngrok 加上「使用者真實的 IP」
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        request.visitor_ip = ip
        request.is_internal = ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172.")
        #print(f"🔍 來源 IP：{ip}，{'內網' if request.is_internal else '外網'}")
        print("連上此裝置的IP位址:",ip)

    # 註冊 blueprint
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    return app

def get_db():
    global mongo_client
    return mongo_client[os.getenv("MONGO_DB_NAME")]
