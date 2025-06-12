from app import get_db

def find_user_by_username(username):
    db = get_db()
    return db.users.find_one({"username": username})

def get_roles():
    db = get_db()
    return list(db.roles.find())
