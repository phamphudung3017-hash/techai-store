import os
import math
import datetime
import uuid
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId

# Import từ thư mục của bạn
from database.db_config import connect_db
from ai_bot.chatbot import get_sales_response
from ai_bot.data_ingest import ingest_data_to_chroma
from functools import wraps

app = Flask(__name__)
app.secret_key = "chuoi_bao_mat_vo_cung_bi_mat_2" 

# Cấu hình thư mục lưu ảnh upload
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db = connect_db()

# --- DECORATOR KIỂM TRA QUYỀN ADMIN ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session.get('role') != 'admin':
            flash("⚠️ Bạn không có quyền truy cập vào trang Quản trị!", "danger")
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# CÁC ROUTE DÀNH CHO KHÁCH HÀNG (USER)
# ==========================================
@app.route('/')
def home():
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort', '') # Bắt tham số sắp xếp
    per_page = 6
    
    if db is not None:
        total_products = db["products"].count_documents({})
        total_pages = math.ceil(total_products / per_page) if total_products > 0 else 1
        skip = (page - 1) * per_page
        
        # Xử lý sắp xếp (Sort)
        cursor = db["products"].find()
        if sort_by == 'asc':
            cursor = cursor.sort("giá", 1)  # Giá tăng dần
        elif sort_by == 'desc':
            cursor = cursor.sort("giá", -1) # Giá giảm dần
            
        products = list(cursor.skip(skip).limit(per_page))
        categories = sorted(list(set([p.get("danh_mục", "") for p in db["products"].find() if p.get("danh_mục")])))
    else:
        products, categories, total_pages = [], [], 1
    
    chat_history = []
    if 'username' in session and db is not None:
        user = db["users"].find_one({"username": session['username']})
        if user and "chat_history" in user:
            chat_history = user["chat_history"]

    # Truyền thêm sort_by sang giao diện để hiển thị
    return render_template('index.html', products=products, categories=categories, current_category="Tất cả sản phẩm", chat_history=chat_history, page=page, total_pages=total_pages, base_url="/", current_sort=sort_by)

@app.route('/category/<cat_name>')
def category(cat_name):
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort', '')
    per_page = 6
    
    if db is not None:
        total_products = db["products"].count_documents({"danh_mục": cat_name})
        total_pages = math.ceil(total_products / per_page) if total_products > 0 else 1
        skip = (page - 1) * per_page
        
        # Xử lý sắp xếp
        cursor = db["products"].find({"danh_mục": cat_name})
        if sort_by == 'asc':
            cursor = cursor.sort("giá", 1)
        elif sort_by == 'desc':
            cursor = cursor.sort("giá", -1)
            
        products = list(cursor.skip(skip).limit(per_page))
        categories = sorted(list(set([p.get("danh_mục", "") for p in db["products"].find() if p.get("danh_mục")])))
    else:
        products, categories, total_pages = [], [], 1
    
    chat_history = []
    if 'username' in session and db is not None:
        user = db["users"].find_one({"username": session['username']})
        if user and "chat_history" in user:
            chat_history = user["chat_history"]

    return render_template('index.html', products=products, categories=categories, current_category=cat_name, chat_history=chat_history, page=page, total_pages=total_pages, base_url=f"/category/{cat_name}", current_sort=sort_by)
@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    if query and db is not None:
        regex_pattern = {"$regex": query, "$options": "i"}
        products = list(db["products"].find({
            "$or": [
                {"tên_sản_phẩm": regex_pattern},
                {"danh_mục": regex_pattern},
                {"thương_hiệu": regex_pattern},
                {"mô_tả": regex_pattern}
            ]
        }))
    else:
        products = []

    categories = sorted(list(set([p.get("danh_mục", "") for p in db["products"].find() if p.get("danh_mục")]))) if db is not None else []
    
    chat_history = []
    if 'username' in session and db is not None:
        user = db["users"].find_one({"username": session['username']})
        if user and "chat_history" in user:
            chat_history = user["chat_history"]

    return render_template('index.html', products=products, categories=categories, current_category=f"🔍 Kết quả tìm kiếm cho: '{query}'", chat_history=chat_history, page=1, total_pages=1, base_url="/search")

@app.route('/product/<id_sp>')
def product_detail(id_sp):
    product = db["products"].find_one({"id_sp": id_sp}) if db is not None else None
    reviews = list(db["reviews"].find({"id_sp": id_sp}).sort("ngày_đăng", -1)) if db is not None else []
    
    avg_rating = 0
    if len(reviews) > 0:
        avg_rating = round(sum(int(r['đánh_giá']) for r in reviews) / len(reviews), 1)

    # --- BỔ SUNG: TRUY XUẤT 4 SẢN PHẨM CÙNG DANH MỤC (SẢN PHẨM LIÊN QUAN) ---
    related_products = []
    if product and db is not None:
        cat_name = product.get('danh_mục', '')
        # Tìm sản phẩm cùng danh mục, dùng $ne (not equal) để loại trừ chính sản phẩm đang xem
        related_products = list(db["products"].find({
            "danh_mục": cat_name,
            "id_sp": {"$ne": id_sp}
        }).limit(4))
        
    return render_template('detail.html', 
                           product=product, 
                           reviews=reviews, 
                           avg_rating=avg_rating, 
                           related_products=related_products)
@app.route('/add_review/<id_sp>', methods=['POST'])
def add_review(id_sp):
    if 'username' not in session:
        flash("⚠️ Bạn cần đăng nhập để đánh giá sản phẩm!", "warning")
        return redirect(url_for('login'))
        
    rating = request.form.get('rating')
    comment = request.form.get('comment')
    
    if db is not None:
        db["reviews"].insert_one({
            "id_sp": id_sp,
            "tài_khoản": session['username'],
            "đánh_giá": int(rating),
            "bình_luận": comment,
            "ngày_đăng": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        flash("✅ Cảm ơn bạn đã đánh giá sản phẩm!", "success")
        
    return redirect(url_for('product_detail', id_sp=id_sp))

# ==========================================
# CÁC ROUTE TÀI KHOẢN (ĐĂNG NHẬP / ĐĂNG KÝ)
# ==========================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if db["users"].find_one({"username": username}):
            flash("Tên đăng nhập đã tồn tại!", "danger")
            return redirect(url_for('register'))
        
        hashed_pw = generate_password_hash(password)
        db["users"].insert_one({"username": username, "password": hashed_pw, "role": "user", "chat_history": []})
        flash("Đăng ký thành công! Hãy đăng nhập.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db["users"].find_one({"username": username})
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            session['role'] = user.get('role', 'user')
            return redirect(url_for('home'))
        else:
            flash("Sai tài khoản hoặc mật khẩu!", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('home'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session:
        flash("Vui lòng đăng nhập để xem thông tin cá nhân!", "warning")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        fullname = request.form.get('fullname', '')
        phone = request.form.get('phone', '')
        address = request.form.get('address', '')
        
        if db is not None:
            # Cập nhật thông tin vào bảng users
            db["users"].update_one(
                {"username": session['username']},
                {"$set": {
                    "fullname": fullname,
                    "phone": phone,
                    "address": address
                }}
            )
            flash("✅ Đã cập nhật thông tin cá nhân thành công!", "success")
        return redirect(url_for('profile'))
    
    # Lấy thông tin user hiện tại và danh sách đơn hàng
    if db is not None:
        user_info = db["users"].find_one({"username": session['username']})
        user_orders = list(db["orders"].find({"tài_khoản": session['username']}).sort("ngày_đặt", -1))
    else:
        user_info, user_orders = {}, []
        
    return render_template('profile.html', orders=user_orders, user_info=user_info)

# ==========================================
# CÁC ROUTE GIỎ HÀNG & THANH TOÁN
# ==========================================

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'username' not in session:
        return jsonify({"status": "error", "message": "⚠️ Vui lòng đăng nhập để thêm sản phẩm vào giỏ hàng!"})
        
    data = request.json
    if 'cart' not in session: session['cart'] = []
    
    # Kỹ thuật gộp sản phẩm: Nếu sản phẩm đã có, chỉ tăng số lượng
    found = False
    for item in session['cart']:
        if item['id'] == data.get('id'):
            item['quantity'] = item.get('quantity', 1) + 1
            found = True
            break
            
    # Nếu là sản phẩm mới tinh thì thêm vào giỏ
    if not found:
        session['cart'].append({
            'id': data.get('id'), 
            'name': data.get('name'), 
            'price': data.get('price'), 
            'image': data.get('image'),
            'quantity': 1  # Mặc định số lượng là 1
        })
        
    session.modified = True 
    return jsonify({"status": "success"})

@app.route('/cart')
def view_cart():
    cart = session.get('cart', [])
    # Tính tổng tiền phải nhân với số lượng
    total_price = sum(item['price'] * item.get('quantity', 1) for item in cart)
    return render_template('cart.html', cart=cart, total_price=total_price)

# CHỨC NĂNG MỚI: Tăng/Giảm số lượng
@app.route('/update_cart/<int:index>/<action>')
def update_cart(index, action):
    if 'cart' in session and 0 <= index < len(session['cart']):
        if action == 'increase':
            session['cart'][index]['quantity'] = session['cart'][index].get('quantity', 1) + 1
        elif action == 'decrease':
            session['cart'][index]['quantity'] = session['cart'][index].get('quantity', 1) - 1
            # Nếu giảm về 0 thì tự động xóa khỏi giỏ
            if session['cart'][index]['quantity'] <= 0:
                session['cart'].pop(index)
        session.modified = True
    return redirect(url_for('view_cart'))

# CHỨC NĂNG MỚI: Xóa hẳn 1 sản phẩm
@app.route('/remove_cart_item/<int:index>')
def remove_cart_item(index):
    if 'cart' in session and 0 <= index < len(session['cart']):
        session['cart'].pop(index)
        session.modified = True
        flash(" Đã xóa sản phẩm khỏi giỏ hàng!", "info")
    return redirect(url_for('view_cart'))

@app.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)
    return redirect(url_for('home'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'username' not in session:
        flash("⚠️ Vui lòng đăng nhập tài khoản để tiến hành thanh toán!", "warning")
        return redirect(url_for('login'))

    if 'cart' not in session or len(session['cart']) == 0:
        flash("Giỏ hàng đang trống!", "warning")
        return redirect(url_for('home'))

    # Tính lại tổng tiền (có nhân với số lượng)
    total_price = sum(item['price'] * item.get('quantity', 1) for item in session['cart'])
    
    voucher_info = session.get('voucher', None)
    discount = voucher_info['discount'] if voucher_info else 0
    final_total = max(0, total_price - discount)

    if request.method == 'POST':
        order_id = "DH-" + str(uuid.uuid4().hex[:6]).upper()
        order_data = {
            "id_đơn_hàng": order_id,
            "tài_khoản": session.get('username'),
            "khách_hàng": request.form['fullname'],
            "số_điện_thoại": request.form['phone'],
            "địa_chỉ": request.form['address'],
            "phương_thức_thanh_toán": request.form['payment_method'],
            "sản_phẩm": session['cart'], # Cấu trúc này giờ đã có thêm 'quantity'
            "tổng_tiền_gốc": total_price,
            "mã_giảm_giá": voucher_info['code'] if voucher_info else None,
            "số_tiền_giảm": discount,
            "tổng_tiền": final_total,
            "trạng_thái": "Chờ duyệt",
            "ngày_đặt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        db["orders"].insert_one(order_data)
        
        session.pop('cart', None)
        session.pop('voucher', None)
        
        flash(f"🎉 Đặt hàng thành công! Mã đơn của bạn là {order_id}", "success")
        return render_template('order_success.html', order_id=order_id, order_data=order_data)

    user_info = db["users"].find_one({"username": session['username']}) if 'username' in session and db is not None else {}
    
    return render_template('checkout.html', total_price=total_price, discount=discount, final_total=final_total, voucher_info=voucher_info, user_info=user_info)
@app.route('/apply_voucher', methods=['POST'])
def apply_voucher():
    code = request.form.get('voucher_code', '').strip().upper()
    cart = session.get('cart', [])
    total_price = sum(item['price'] for item in cart)
    
    if not code:
        flash("⚠️ Vui lòng nhập mã giảm giá!", "warning")
        return redirect(url_for('checkout'))
        
    voucher = db["vouchers"].find_one({"code": code}) if db is not None else None
    
    if not voucher:
        flash("❌ Mã giảm giá không tồn tại!", "danger")
        return redirect(url_for('checkout'))
        
    min_order = voucher.get('min_order', 0)
    if total_price < min_order:
        flash(f"⚠️ Mã này chỉ áp dụng cho đơn hàng từ {min_order:,.0f}đ trở lên!", "warning")
        return redirect(url_for('checkout'))
        
    # Tính tiền giảm
    discount = 0
    if voucher['type'] == 'fixed':
        discount = voucher['value']
    elif voucher['type'] == 'percent':
        discount = total_price * (voucher['value'] / 100.0)
        
    # Lưu voucher vào session
    session['voucher'] = {
        'code': voucher['code'],
        'discount': discount,
        'description': voucher.get('description', '')
    }
    session.modified = True
    
    flash(f" Áp dụng mã '{code}' thành công! Được giảm {discount:,.0f}đ.", "success")
    return redirect(url_for('checkout'))

@app.route('/remove_voucher')
def remove_voucher():
    session.pop('voucher', None)
    flash("Đã hủy áp dụng mã giảm giá.", "info")
    return redirect(url_for('checkout'))

# ==========================================
# CÁC ROUTE QUẢN TRỊ ADMIN (RBAC)
# ==========================================

@app.route('/admin')
@admin_required
def admin_dashboard():
    if db is not None:
        products = list(db["products"].find())
        orders = list(db["orders"].find())
        users = list(db["users"].find())
        brands = list(db["brands"].find())
        
        total_products = len(products)
        total_orders = len(orders)
        pending_orders = sum(1 for o in orders if o.get('trạng_thái') == 'Chờ duyệt')
        completed_orders = sum(1 for o in orders if o.get('trạng_thái') == 'Đã hoàn thành')
        total_revenue = sum(o.get('tổng_tiền', 0) for o in orders if o.get('trạng_thái') == 'Đã hoàn thành')
        total_users = len(users)

        # TÍNH DOANH THU THỰC TẾ 7 NGÀY GẦN NHẤT
        today = datetime.date.today()
        chart_labels = []
        chart_revenue = []
        
        for i in range(6, -1, -1): # Vòng lặp lùi từ 6 ngày trước đến hôm nay
            day = today - datetime.timedelta(days=i)
            # Thêm nhãn ngày/tháng (VD: 20/08) cho trục X của biểu đồ
            chart_labels.append(day.strftime("%d/%m"))
            
            day_revenue = 0
            # Chuỗi ngày format chuẩn để so sánh (VD: "2026-08-20")
            day_str = day.strftime("%Y-%m-%d") 
            
            for o in orders:
                # Quét các đơn đã hoàn thành và có ngày đặt khớp với ngày đang xét
                if o.get('trạng_thái') == 'Đã hoàn thành' and o.get('ngày_đặt', '').startswith(day_str):
                    day_revenue += o.get('tổng_tiền', 0)
                    
            # Thêm doanh thu của ngày đó vào danh sách vẽ biểu đồ
            chart_revenue.append(day_revenue)
        # --------------------------------------------------------

        stats = {
            "total_products": total_products,
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "completed_orders": completed_orders,
            "total_revenue": total_revenue,
            "total_users": total_users,
            "total_brands": len(brands)
        }
    else:
        stats, chart_labels, chart_revenue = {}, [], []

    return render_template('admin_dashboard.html', stats=stats, chart_labels=chart_labels, chart_revenue=chart_revenue, active_page="dashboard")
@app.route('/admin/products')
@admin_required
def admin_products():
    products = list(db["products"].find()) if db is not None else []
    return render_template('admin_products.html', products=products, active_page="products")

@app.route('/admin/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    if request.method == 'POST':
        id_sp = request.form['id_sp']
        image_url = request.form.get('hình_ảnh', '')

        file = request.files.get('hinh_anh_file')
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_name = f"{id_sp}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], save_name)
            file.save(file_path)
            image_url = f"/static/uploads/{save_name}"

        db["products"].insert_one({
            "id_sp": id_sp,
            "tên_sản_phẩm": request.form['tên_sản_phẩm'],
            "danh_mục": request.form['danh_mục'],
            "thương_hiệu": request.form['thương_hiệu'],
            "giá": float(request.form['giá']),
            "hình_ảnh": image_url,
            "mô_tả": request.form['mô_tả'],
            "thông_số": request.form['thông_số']
        })
        try:
            ingest_data_to_chroma()
            flash("Thêm sản phẩm thành công và đã đồng bộ AI!", "success")
        except Exception as e:
            flash(f"Lỗi đồng bộ AI: {e}", "warning")
        return redirect(url_for('admin_products'))
        
    brands = list(db["brands"].find().sort("name", 1)) if db is not None else []
    return render_template('admin_product_form.html', product=None, action="Thêm", brands=brands)

@app.route('/admin/edit/<id_sp>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(id_sp):
    product = db["products"].find_one({"id_sp": id_sp})
    if not product:
        flash("Sản phẩm không tồn tại!", "danger")
        return redirect(url_for('admin_products'))
        
    if request.method == 'POST':
        image_url = request.form.get('hình_ảnh', product.get('hình_ảnh', ''))

        file = request.files.get('hinh_anh_file')
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_name = f"{id_sp}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], save_name)
            file.save(file_path)
            image_url = f"/static/uploads/{save_name}"

        db["products"].update_one({"id_sp": id_sp}, {"$set": {
            "tên_sản_phẩm": request.form['tên_sản_phẩm'],
            "danh_mục": request.form['danh_mục'],
            "thương_hiệu": request.form['thương_hiệu'],
            "giá": float(request.form['giá']),
            "hình_ảnh": image_url,
            "mô_tả": request.form['mô_tả'],
            "thông_số": request.form['thông_số']
        }})
        try:
            ingest_data_to_chroma()
            flash("Cập nhật sản phẩm thành công và đã đồng bộ AI!", "success")
        except Exception as e:
            flash(f"Lỗi đồng bộ AI: {e}", "warning")
        return redirect(url_for('admin_products'))
        
    brands = list(db["brands"].find().sort("name", 1)) if db is not None else []
    return render_template('admin_product_form.html', product=product, action="Sửa", brands=brands)

@app.route('/admin/delete/<id_sp>')
@admin_required
def admin_delete_product(id_sp):
    db["products"].delete_one({"id_sp": id_sp})
    try:
        ingest_data_to_chroma()
        flash("Đã xóa sản phẩm và cập nhật bộ nhớ AI!", "success")
    except Exception as e:
        flash(f"Lỗi đồng bộ AI: {e}", "warning")
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
@admin_required
def admin_orders():
    orders = list(db["orders"].find().sort("ngày_đặt", -1)) if db is not None else []
    return render_template('admin_orders.html', orders=orders, active_page="orders")

@app.route('/admin/orders/update/<order_id>', methods=['POST'])
@admin_required
def update_order_status(order_id):
    new_status = request.form.get('status')
    if db is not None:
        db["orders"].update_one({"id_đơn_hàng": order_id}, {"$set": {"trạng_thái": new_status}})
        flash(f"✅ Cập nhật trạng thái đơn {order_id} thành '{new_status}'!", "success")
    return redirect(url_for('admin_orders'))

@app.route('/admin/brands')
@admin_required
def admin_brands():
    brands = list(db["brands"].find().sort("name", 1)) if db is not None else []
    return render_template('admin_brands.html', brands=brands, active_page="brands")

@app.route('/admin/brands/add', methods=['POST'])
@admin_required
def admin_add_brand():
    brand_name = request.form.get('name', '').strip()
    if brand_name and db is not None:
        if db["brands"].find_one({"name": {"$regex": f"^{brand_name}$", "$options": "i"}}):
            flash(f"⚠️ Thương hiệu '{brand_name}' đã tồn tại!", "warning")
        else:
            db["brands"].insert_one({"name": brand_name})
            flash(f"✅ Đã thêm thương hiệu '{brand_name}'!", "success")
    return redirect(url_for('admin_brands'))

@app.route('/admin/brands/delete/<brand_id>')
@admin_required
def admin_delete_brand(brand_id):
    if db is not None:
        db["brands"].delete_one({"_id": ObjectId(brand_id)})
        flash("🗑️ Đã xóa thương hiệu!", "success")
    return redirect(url_for('admin_brands'))

@app.route('/admin/users')
@admin_required
def admin_users():
    users = list(db["users"].find()) if db is not None else []
    return render_template('admin_users.html', users=users, active_page="users")

@app.route('/admin/users/delete/<username>')
@admin_required
def admin_delete_user(username):
    if username == session.get('username'):
        flash("⚠️ Bạn không thể xóa tài khoản Admin đang đăng nhập!", "warning")
    else:
        db["users"].delete_one({"username": username})
        flash(f"🗑️ Đã xóa tài khoản '{username}'!", "success")
    return redirect(url_for('admin_users'))

@app.route('/admin/sync_ai')
@admin_required
def admin_sync_ai():
    try:
        ingest_data_to_chroma()
        flash("Đã đồng bộ toàn bộ dữ liệu sang AI ChromaDB!", "success")
    except Exception as e:
        flash(f"Lỗi đồng bộ AI: {e}", "danger")
    return redirect(url_for('admin_dashboard'))
# ==========================================
# CÁC ROUTE DANH SÁCH YÊU THÍCH (WISHLIST)
# ==========================================

# 1. Hàm tự động đẩy biến user_wishlist vào TẤT CẢ các trang HTML (Context Processor)
@app.context_processor
def inject_wishlist():
    wishlist = []
    if 'username' in session and db is not None:
        user = db["users"].find_one({"username": session['username']})
        if user:
            wishlist = user.get('wishlist', [])
    return dict(user_wishlist=wishlist)

# 2. API Xử lý khi khách bấm nút Thả tim (Thêm / Xóa)
@app.route('/toggle_wishlist/<id_sp>', methods=['POST'])
def toggle_wishlist(id_sp):
    if 'username' not in session:
        return jsonify({"status": "error", "message": "Vui lòng đăng nhập để thả tim sản phẩm!"})
    
    if db is not None:
        user = db["users"].find_one({"username": session['username']})
        wishlist = user.get('wishlist', [])
        
        if id_sp in wishlist:
            wishlist.remove(id_sp)
            action = "removed"
        else:
            wishlist.append(id_sp)
            action = "added"
            
        # Cập nhật mảng wishlist vào bảng users
        db["users"].update_one({"username": session['username']}, {"$set": {"wishlist": wishlist}})
        return jsonify({"status": "success", "action": action})
    return jsonify({"status": "error"})

# 3. Giao diện trang Danh sách Yêu thích
@app.route('/wishlist')
def view_wishlist():
    if 'username' not in session:
        flash("Vui lòng đăng nhập để xem danh sách yêu thích!", "warning")
        return redirect(url_for('login'))
        
    if db is not None:
        user = db["users"].find_one({"username": session['username']})
        wishlist_ids = user.get('wishlist', [])
        # Lấy thông tin các sản phẩm nằm trong mảng wishlist
        products = list(db["products"].find({"id_sp": {"$in": wishlist_ids}}))
    else:
        products = []
        
    return render_template('wishlist.html', products=products)

# ==========================================
# CÁC API AI & CHATBOT
# ==========================================

@app.route('/chat', methods=['POST'])
def chat():
    user_msg = request.json.get('message')
    bot_reply = get_sales_response(user_msg)
    
    if 'username' in session and db is not None:
        db["users"].update_one(
            {"username": session['username']},
            {"$push": {"chat_history": {"$each": [
                {"sender": "user", "msg": user_msg},
                {"sender": "bot", "msg": bot_reply}
            ]}}}
        )
        
    return jsonify({"reply": bot_reply})

if __name__ == '__main__':
    app.run(debug=True)
