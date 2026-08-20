import os
import re
from dotenv import load_dotenv
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

# Gọi kết nối cơ sở dữ liệu để tra cứu đơn hàng
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_config import connect_db

# 1. Tải API Key
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_data")
db = connect_db()

def get_sales_response(user_question):
    try:
        # --- TÍNH NĂNG MỚI: TRA CỨU ĐƠN HÀNG TỰ ĐỘNG ---
        order_context = ""
        # Dùng Regex để tìm các mã có chữ "DH-" kèm theo khoảng ký tự phía sau
        match = re.search(r'(DH-[A-Za-z0-9]+)', user_question.upper())
        
        if match and db is not None:
            order_id = match.group(1)
            order = db["orders"].find_one({"id_đơn_hàng": order_id})
            
            if order:
                # Nếu tìm thấy, nhồi thông tin đơn hàng vào não AI
                danh_sach_sp = ", ".join([item['name'] for item in order['sản_phẩm']])
                order_context = f"""
                THÔNG TIN ĐƠN HÀNG KHÁCH ĐANG HỎI (Mã: {order_id}):
                - Tình trạng hiện tại: {order['trạng_thái']}
                - Tên người nhận: {order['khách_hàng']}
                - Số điện thoại: {order['số_điện_thoại']}
                - Địa chỉ: {order['địa_chỉ']}
                - Phương thức thanh toán: {order['phương_thức_thanh_toán']}
                - Sản phẩm đã mua: {danh_sach_sp}
                - Tổng tiền: {order['tổng_tiền']} VNĐ
                - Ngày đặt: {order['ngày_đặt']}
                """
            else:
                order_context = f"Hệ thống báo cáo: Không tìm thấy đơn hàng nào có mã {order_id} trong cơ sở dữ liệu."

        # --- LUỒNG RAG TRUYỀN THỐNG: TRA CỨU SẢN PHẨM ---
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001", 
            google_api_key=GEMINI_API_KEY
        )

        vector_db = Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=embeddings
        )

        search_results = vector_db.similarity_search(user_question, k=2) 
        context = ""
        for doc in search_results:
            context += doc.page_content + "\n"

        # --- GỌI MÔ HÌNH CHAT GEMINI ---
        llm = ChatGoogleGenerativeAI(
            model="models/gemini-3.5-flash",
            google_api_key=GEMINI_API_KEY,
            temperature=0.7
        )

        prompt = f"""
        Bạn là một nhân viên tư vấn bán hàng thiết bị công nghệ và linh kiện điện tử nhiệt tình, am hiểu kỹ thuật, xưng em gọi anh/chị.
        
        Dưới đây là thông tin các sản phẩm hiện có trong cửa hàng:
        ---------------------
        {context}
        ---------------------
        
        {order_context}
        
        Khách hàng hỏi: "{user_question}"
        
        Nhiệm vụ của bạn:
        1. Nếu khách hỏi về sản phẩm: Dựa VÀO ĐÚNG thông tin sản phẩm ở trên để tư vấn thông số, tính năng và giá cả cho khách hàng.
        2. Nếu khách hỏi về đơn hàng: Dựa vào "THÔNG TIN ĐƠN HÀNG" ở trên để báo cáo tình trạng đơn cho khách một cách lịch sự, báo rõ trạng thái, ngày đặt và tổng tiền. Nếu không tìm thấy, hãy xin lỗi khách.
        3. TUYỆT ĐỐI KHÔNG tự bịa ra sản phẩm, thông số hay trạng thái đơn hàng.
        """

        response = llm.invoke(prompt)
        
        answer = response.content
        if isinstance(answer, list):
            return answer[0].get('text', '')
        else:
            return answer

    except Exception as e:
        return f"Lỗi hệ thống AI: {e}"

if __name__ == "__main__":
    print("🤖 CHATBOT RAG ĐÃ SẴN SÀNG TƯ VẤN VÀ TRA CỨU ĐƠN HÀNG!")
    # Test thử trực tiếp
    print(get_sales_response("Kiểm tra giúp mình đơn hàng DH-TEST1234"))