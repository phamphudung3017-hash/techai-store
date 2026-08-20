import os
from pymongo import MongoClient

def connect_db():
    # Ưu tiên lấy biến môi trường từ Render, nếu không có thì mặc định lấy localhost (khi chạy ở máy nhà)
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    
    try:
        # serverSelectionTimeoutMS=5000 giúp hệ thống báo lỗi nhanh hơn nếu rớt mạng (5 giây thay vì 30 giây)
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        
        # Tạo/Kết nối vào database có tên là 'techai_store'
        db = client["ecommerce_db"] 
        return db
    except Exception as e:
        print(f"❌ Lỗi kết nối MongoDB: {e}")
        return None
