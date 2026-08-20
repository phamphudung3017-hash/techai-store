import os
from pymongo import MongoClient

def connect_db():
    # Lấy biến môi trường từ Render, mặc định localhost nếu chạy ở máy nhà
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    
    try:
        # KỸ THUẬT "VIÊN ĐẠN BẠC": Bỏ qua kiểm tra chứng chỉ SSL khắt khe trên Server
        client = MongoClient(
            MONGO_URI, 
            serverSelectionTimeoutMS=5000,
            tls=True,
            tlsAllowInvalidCertificates=True  # <--- Dòng lệnh "cứu cánh"
        )
        
        # Nhớ giữ nguyên 'techai_store' hoặc đổi thành tên database của bạn nhé
        db = client["techai_store"] 
        return db
    except Exception as e:
        print(f"❌ Lỗi kết nối MongoDB: {e}")
        return None