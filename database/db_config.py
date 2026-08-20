import os
import certifi
from pymongo import MongoClient

def connect_db():
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    
    try:
        # Code chuẩn mực cho Python 3.11 + MongoDB Atlas
        client = MongoClient(
            MONGO_URI, 
            serverSelectionTimeoutMS=5000,
            tls=True,
            tlsCAFile=certifi.where()
        )
        
        # Đảm bảo tên database đúng với tên bạn đang dùng
        db = client["techai_store"] 
        return db
    except Exception as e:
        print(f"❌ Lỗi kết nối MongoDB: {e}")
        return None