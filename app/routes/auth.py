from flask import Blueprint, request, jsonify, render_template
from app.models.user import find_user_by_username
from app.utils.password import verify_password
from werkzeug.security import generate_password_hash
from app import get_db
from bson.json_util import dumps
from bson.objectid import ObjectId
from datetime import datetime

auth_bp = Blueprint("auth", __name__)

# 顯示註冊畫面
@auth_bp.route("/register-page", methods=["GET"])
def show_register_page():
    return render_template("register.html")

# 顯示 register.html 頁面
@auth_bp.route("/register", methods=["GET"])
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

        # 如果角色是 admin，跳轉到 apply 頁面
        if user.get("role") == "admin":
            return jsonify({"message": "登入成功", "redirect": "/auth/apply"}), 200

        return jsonify({"message": "登入成功", "username": username}), 200
    except Exception as e:
        return jsonify({"message": f"登入失敗：{str(e)}"}), 500


# 回傳前端 HTML 頁面（登入介面）
@auth_bp.route("/login-page", methods=["GET"])
def login_page():
    return render_template("login.html")

# 顯示 apply.html 頁面
@auth_bp.route("/apply", methods=["GET"])
def apply_page():
    return render_template("apply.html")

# 顯示 modify.html 頁面
@auth_bp.route("/modify", methods=["GET"])
def modify_page():
    return render_template("modify.html")

# 獲取所有使用者
@auth_bp.route("/users", methods=["GET"])
def get_users():
    db = get_db()
    users = list(db.users.find({}, {"_id": 0}))  # 不返回 _id 欄位
    return jsonify(users)

# 刪除使用者
@auth_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    db = get_db()
    result = db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        return jsonify({"message": "使用者不存在"}), 404
    return jsonify({"message": "使用者已刪除"})

# 修改使用者（示例：更新角色）
@auth_bp.route("/users/<int:user_id>", methods=["PUT"])
def modify_user(user_id):
    data = request.get_json()
    new_role = data.get("role")
    if not new_role:
        return jsonify({"message": "缺少角色資訊"}), 400

    db = get_db()
    result = db.users.update_one({"id": user_id}, {"$set": {"role": new_role}})
    if result.matched_count == 0:
        return jsonify({"message": "使用者不存在"}), 404
    return jsonify({"message": "使用者已更新"})

# 審核使用者
@auth_bp.route("/users/<string:username>/approve", methods=["POST"])
def approve_user(username):
    db = get_db()
    user = db.apply.find_one({"username": username})
    if not user:
        return jsonify({"message": "使用者不存在"}), 404

    new_status = user.get("review_status", 0) + 1
    db.apply.update_one({"username":username}, {"$set": {"review_status": new_status}})
    return jsonify({"message": "已審核", "review_status": new_status})

# 修改特定使用者的資料（根據索引，從 1 開始）
@auth_bp.route("/users/index/<int:index>", methods=["PUT"])
def modify_user_by_index(index):
    data = request.get_json()
    update_fields = data.get("update_fields", {})

    if not update_fields:
        return jsonify({"message": "缺少更新的資料"}), 400

    db = get_db()
    users = list(db.users.find())

    if index < 1 or index > len(users):
        return jsonify({"message": "索引超出範圍"}), 400

    user_id = users[index - 1]["id"]  # 根據索引找到使用者 ID
    result = db.users.update_one({"id": user_id}, {"$set": update_fields})

    if result.matched_count == 0:
        return jsonify({"message": "使用者不存在"}), 404

    return jsonify({"message": "使用者資料已更新"})

# 獲取使用者資訊，返回符合格式的 JSON
@auth_bp.route("/users/details", methods=["GET"])
def get_user_details():
    db = get_db()
    users = db.users.find()
    role_collection = db.roles  # 獲取 apply 集合
    apply_collection = db.apply  # 獲取 apply 集合

    formatted_users = []
    for user in users:
        # 根據用戶名查找 apply 集合中的對應文件
        role_data = role_collection.find_one({"username": user["username"]})
        role = role_data["role"] if role_data and "role" in role_data else 0

        # 根據用戶名查找 apply 集合中的對應文件
        apply_data = apply_collection.find_one({"username": user["username"]})
        review_status = apply_data["review_status"] if apply_data and "review_status" in apply_data else 0
        requested_permissions = apply_data["requested_permissions"] if apply_data and "requested_permissions" in apply_data else 0

        formatted_users.append({
            "user_id": str(user["_id"]),
            "username": user.get("username", ""),
            "requested_role": role,
            "requested_permissions": requested_permissions,
            "review_status": review_status,
            "created_at": user["created_at"].isoformat() if "created_at" in user else None
        })

    return jsonify(formatted_users)

# 更新使用者權限
@auth_bp.route("/users/<string:username>/update-permissions", methods=["POST"])
def update_permissions(username):
    db = get_db()
    user = db.apply.find_one({"username": username})
    if not user:
        return jsonify({"message": "使用者不存在"}), 404

    data = request.get_json()
    action = data.get("action")
    permission = data.get("permission")

    if not permission:
        return jsonify({"message": "缺少權限資訊"}), 400

    requested_permissions = user.get("requested_permissions", [])

    if action == "add":
        if permission not in requested_permissions:
            requested_permissions.append(permission)
    elif action == "remove":
        if permission in requested_permissions:
            requested_permissions.remove(permission)

    db.apply.update_one({"username": username}, {"$set": {"requested_permissions": requested_permissions}})

    return jsonify({"message": "權限已更新", "requested_permissions": requested_permissions})
