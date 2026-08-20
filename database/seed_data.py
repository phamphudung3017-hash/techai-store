import os
import sys

# Thêm đường dẫn gốc để Python nhận diện được thư mục database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db_config import connect_db

db = connect_db()

if db is not None:
    products_collection = db["products"]
    
    # Kho sản phẩm Linh kiện & Thiết bị điện tử phong phú
    tech_products = [
        {
            "id_sp": "SP001",
            "tên_sản_phẩm": "Laptop Gaming ASUS ROG Strix G16",
            "danh_mục": "Laptop",
            "thương_hiệu": "ASUS",
            "giá": 34990000,
            "hình_ảnh": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500",
            "mô_tả": "Laptop chơi game hiệu năng đỉnh cao với CPU Intel Gen 13 và card đồ họa RTX 4060.",
            "thông_số": "CPU: Intel Core i7-13650HX | RAM: 16GB DDR5 | SSD: 512GB NVMe | Màn hình: 16 inch FHD+ 165Hz | Card: RTX 4060 8GB | Bảo hành: 24 tháng"
        },
        {
            "id_sp": "SP002",
            "tên_sản_phẩm": "Tai nghe Bluetooth Sony WH-1000XM5",
            "danh_mục": "Tai nghe",
            "thương_hiệu": "Sony",
            "giá": 8490000,
            "hình_ảnh": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500",
            "mô_tả": "Tai nghe chụp tai chống ồn chủ động (ANC) hàng đầu thế giới, thời lượng pin cực trâu.",
            "thông_số": "Thời lượng pin: 30 giờ | Kết nối: Bluetooth 5.2, AUX 3.5mm | Chống ồn: V1 Processor | Trọng lượng: 250g | Bảo hành: 12 tháng"
        },
        {
            "id_sp": "SP003",
            "tên_sản_phẩm": "Bàn phím cơ AKKO 3068B Plus Prunus Lannesiana",
            "danh_mục": "Bàn phím",
            "thương_hiệu": "AKKO",
            "giá": 1650000,
            "hình_ảnh": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500",
            "mô_tả": "Bàn phím cơ không dây layout 65% nhỏ gọn, phối màu Sakura cực đẹp, hỗ trợ Hotswap.",
            "thông_số": "Chế độ kết nối: Type-C / Bluetooth 5.0 / 2.4Ghz | Switch: AKKO CS Jelly Pink | LED: RGB | Dung lượng pin: 1800mAh | Bảo hành: 12 tháng"
        },
        {
            "id_sp": "SP004",
            "tên_sản_phẩm": "Chuột không dây Logitech MX Master 3S",
            "danh_mục": "Chuột",
            "thương_hiệu": "Logitech",
            "giá": 2450000,
            "hình_ảnh": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500",
            "mô_tả": "Dòng chuột công thái học cao cấp dành cho lập trình viên và thiết kế đồ họa.",
            "thông_số": "Độ phân giải: 8000 DPI | Nút cuộn: MagSpeed cuộn 1000 dòng/giây | Click: Chống ồn Silent Touch | Kết nối: Logi Bolt / Bluetooth | Bảo hành: 12 tháng"
        },
        {
            "id_sp": "SP005",
            "tên_sản_phẩm": "Màn hình Gaming LG UltraGear 27GP850-B 27 inch",
            "danh_mục": "Màn hình",
            "thương_hiệu": "LG",
            "giá": 8990000,
            "hình_ảnh": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=500",
            "mô_tả": "Màn hình chuyên game Nano IPS độ phân giải 2K, tốc độ phản hồi 1ms siêu mượt.",
            "thông_số": "Kích thước: 27 inch | Độ phân giải: QHD (2560 x 1440) | Tấm nền: Nano IPS | Tần số quét: 180Hz (Overclock) | Thời gian phản hồi: 1ms | Bảo hành: 24 tháng"
        },
        {
            "id_sp": "SP006",
            "tên_sản_phẩm": "Card màn hình MSI RTX 4070 Ti SUPER 16G Ventus 3X",
            "danh_mục": "Linh kiện PC",
            "thương_hiệu": "MSI",
            "giá": 23990000,
            "hình_ảnh": "https://images.unsplash.com/photo-1591488320449-011701bb6704?w=500",
            "mô_tả": "VGA đồ họa mạnh mẽ cân mọi tựa game 4K AAA và xử lý đồ họa, dựng video 8K.",
            "thông_số": "Bộ nhớ VRAM: 16GB GDDR6X | Bus bộ nhớ: 256-bit | Nhân CUDA: 8448 | Cổng kết nối: DisplayPort x 3, HDMI x 1 | Nguồn đề xuất: 700W | Bảo hành: 36 tháng"
        }
    ]
    
    # Xóa dữ liệu cũ và nạp kho dữ liệu mới
    products_collection.delete_many({})
    products_collection.insert_many(tech_products)
    print("✅ ĐÃ NÂNG CẤP KHO HÀNG LINH KIỆN ĐIỆN TỬ THÀNH CÔNG TRÊN MONGODB ATLAS!")
else:
    print("❌ Không thể kết nối MongoDB.")