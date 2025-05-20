from flask import Flask
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

    # 註冊 blueprint
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    return app

def get_db():
    global mongo_client
    return mongo_client[os.getenv("MONGO_DB_NAME")]
