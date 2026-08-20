import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Thêm đường dẫn gốc để Python nhận diện được thư mục 'database'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_config import connect_db

# Tải các thư viện AI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

# Tự động tìm file .env ở thư mục gốc
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def ingest_data_to_chroma():
    print("⏳ Đang kết nối tới MongoDB...")
    db = connect_db()
    if db is None:
        return

    # Lấy toàn bộ sản phẩm
    products = list(db["products"].find())
    if not products:
        print("❌ Chưa có sản phẩm nào trong cơ sở dữ liệu.")
        return

    print(f"✅ Tìm thấy {len(products)} sản phẩm. Đang chuẩn bị dịch sang ngôn ngữ AI (Vector)...")

    # Chuẩn bị văn bản (documents) để đưa cho AI
    texts = []
    metadatas = []
    
    for prod in products:
        # Gom các thông tin lại thành 1 đoạn văn bản hoàn chỉnh
        desc = f"Tên sản phẩm: {prod.get('tên_sản_phẩm', '')}. Giá bán: {prod.get('giá', '')} VNĐ. Mô tả chi tiết: {prod.get('mô_tả', '')}"
        texts.append(desc)
        # Lưu kèm ID để truy xuất nếu cần
        metadatas.append({"id": str(prod["_id"]), "name": prod.get("tên_sản_phẩm", "")})

    # Sử dụng mô hình Embedding của Google để dịch văn bản
    # Lưu ý: Mô hình này chuyên dùng để dịch dữ liệu, khác với mô hình chat
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001", 
        google_api_key=GEMINI_API_KEY
    )

    # Nơi lưu trữ bộ nhớ ChromaDB cục bộ
    chroma_path = os.path.join(os.path.dirname(__file__), "chroma_data")
    
    print("🧠 Đang tạo Vector Database và lưu vào máy tính...")
    # Tạo và lưu dữ liệu vào ChromaDB
    vector_db = Chroma.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas,
        persist_directory=chroma_path
    )
    
    print(f"🎉 XONG! Đã lưu thành công dữ liệu vào thư mục: {chroma_path}")
    print("Khung xương RAG đã sẵn sàng để Chatbot sử dụng!")

if __name__ == "__main__":
    ingest_data_to_chroma()