import os
import certifi
from pymongo import MongoClient

def connect_db():
    # Lấy biến môi trường từ Render, mặc định localhost nếu chạy ở máy nhà
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    
    try:
        # Thêm tlsCAFile=certifi.where() để giải quyết triệt để lỗi SSL Handshake
        client = MongoClient(
            MONGO_URI, 
            serverSelectionTimeoutMS=5000,
            tlsCAFile=certifi.where()
        )
        
        # Nhớ đổi 'techai_store' thành tên database thực tế của bạn nhé
        db = client["techai_store"] 
        return db
    except Exception as e:
        print(f"❌ Lỗi kết nối MongoDB: {e}")
        return None