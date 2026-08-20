import os
import certifi
from pymongo import MongoClient

def connect_db():
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    
    try:
        # Tối giản code, mọi cấu hình bảo mật đã được đưa vào chuỗi MONGO_URI
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        
        # Đảm bảo đây đúng là tên database bạn dùng nhé
        db = client["ecommerce_db"] 
        return db
    except Exception as e:
        print(f"❌ Lỗi kết nối MongoDB: {e}")
        return None