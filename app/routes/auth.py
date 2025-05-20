from flask import Blueprint, request, jsonify, render_template
from app.models.user import find_user_by_username
from app.utils.password import verify_password
from werkzeug.security import generate_password_hash
from app import get_db

auth_bp = Blueprint("auth", __name__)

# 顯示註冊畫面
@auth_bp.route("/register-page", methods=["GET"])
def register_page():
    return render_template("register.html")

# 處理註冊 POST
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    team = data.get("team", "")
    location = data.get("location", "")

    if not username or not password:
        return jsonify({"message": "帳號與密碼為必填"}), 400

    db = get_db()
    # 檢查是否已有同名帳號
    if db.users.find_one({"username": username}):
        return jsonify({"message": "帳號已存在"}), 409

    # 預設角色為 user（或 admin 可改）
    role = "user"

    db.users.insert_one({
        "username": username,
        "password_hash": generate_password_hash(password),
        "role": role,
        "attributes": {
            "team": team,
            "location": location
        }
    })

    return jsonify({"message": "註冊成功！請返回登入頁面"})

# 登入 API：接收 JSON 資料
@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()  # 解析前端傳來的 JSON
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"message": "請輸入帳號與密碼"}), 400

        user = find_user_by_username(username)
        if not user:
            return jsonify({"message": "帳號不存在"}), 401

        if not verify_password(password, user["password_hash"]):
            return jsonify({"message": "密碼錯誤"}), 401

        return jsonify({"message": "登入成功", "username": username}), 200
    except Exception as e:
        return jsonify({"message": f"登入失敗：{str(e)}"}), 500


# 回傳前端 HTML 頁面（登入介面）
@auth_bp.route("/login-page", methods=["GET"])
def login_page():
    return render_template("login.html")
