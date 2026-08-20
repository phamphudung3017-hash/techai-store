import os
import sys

# Thêm đường dẫn gốc
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from database.db_config import connect_db

db = connect_db()

if db is not None:
    vouchers_col = db["vouchers"]
    
    # Danh sách voucher mẫu
    initial_vouchers = [
        {
            "code": "TECHAI100K",
            "type": "fixed",         # Giảm tiền cố định
            "value": 100000,         # Giảm 100.000 VNĐ
            "min_order": 500000,     # Đơn tối thiểu 500.000 VNĐ
            "description": "Giảm 100.000đ cho đơn từ 500.000đ"
        },
        {
            "code": "SALE10",
            "type": "percent",       # Giảm theo %
            "value": 10,             # Giảm 10%
            "min_order": 0,          # Không giới hạn đơn tối thiểu
            "description": "Giảm 10% cho mọi đơn hàng"
        }
    ]
    
    vouchers_col.delete_many({})
    vouchers_col.insert_many(initial_vouchers)
    print("✅ ĐÃ TẠO BẢNG 'vouchers' VÀ NẠP MÃ GIẢM GIÁ MẪU THÀNH CÔNG!")
else:
    print("❌ Không thể kết nối MongoDB.")