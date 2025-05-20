from app import get_db

def find_user_by_username(username):
    db = get_db()
    return db.users.find_one({"username": username})
