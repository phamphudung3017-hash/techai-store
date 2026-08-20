import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Tải các biến môi trường từ file .env
load_dotenv()

# Lấy chuỗi kết nối
MONGO_URI = os.getenv("MONGO_URI")

def connect_db():
    try:
        # Kết nối đến MongoDB
        client = MongoClient(MONGO_URI)
        
        # Ping thử để kiểm tra kết nối
        client.admin.command('ping')
        print("🎉 Chúc mừng! Bạn đã kết nối thành công tới MongoDB Atlas!")
        
        # Trỏ tới database và bảng của đồ án
        db = client["ecommerce_db"]
        return db
        
    except Exception as e:
        print("❌ Kết nối thất bại. Lỗi chi tiết:")
        print(e)
        return None

# Chạy thử hàm kết nối
if __name__ == "__main__":
    connect_db()