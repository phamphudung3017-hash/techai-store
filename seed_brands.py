import os
import sys

# Thêm đường dẫn gốc
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from database.db_config import connect_db

db = connect_db()

if db is not None:
    brands_col = db["brands"]
    
    # Danh sách thương hiệu mẫu
    initial_brands = [
        {"name": "ASUS"},
        {"name": "Sony"},
        {"name": "Logitech"},
        {"name": "LG"},
        {"name": "MSI"},
        {"name": "Acer"},
        {"name": "Anker"}
    ]
    
    # Xóa cũ và nạp mới
    brands_col.delete_many({})
    brands_col.insert_many(initial_brands)
    print("✅ ĐÃ TẠO BẢNG 'brands' VÀ NẠP CÁC THƯƠNG HIỆU MẪU THÀNH CÔNG!")
else:
    print("❌ Không thể kết nối MongoDB.")