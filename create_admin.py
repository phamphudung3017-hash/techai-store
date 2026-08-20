import os
import sys
from werkzeug.security import generate_password_hash

# Thêm đường dẫn gốc
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from database.db_config import connect_db

db = connect_db()

if db is not None:
    users_col = db["users"]
    
    admin_username = "admin"
    admin_password = "admin123"  # Mật khẩu tài khoản admin
    
    # Kiểm tra xem tài khoản admin đã tồn tại chưa
    existing_admin = users_col.find_one({"username": admin_username})
    
    if existing_admin:
        # Nếu đã có tài khoản admin, cập nhật role thành admin
        users_col.update_one(
            {"username": admin_username},
            {"$set": {"role": "admin"}}
        )
        print(f"✅ Đã cập nhật quyền ADMIN cho tài khoản '{admin_username}'!")
    else:
        # Tạo mới tài khoản admin
        hashed_pw = generate_password_hash(admin_password)
        users_col.insert_one({
            "username": admin_username,
            "password": hashed_pw,
            "role": "admin",  # Đánh dấu vai trò ADMIN
            "chat_history": []
        })
        print(f"🎉 Đã tạo thành công tài khoản ADMIN!\n- Username: {admin_username}\n- Password: {admin_password}")
else:
    print("❌ Không thể kết nối MongoDB.")