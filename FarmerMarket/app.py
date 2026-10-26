from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import mysql.connector
import os
from config import Config
from PIL import Image
import io
import time
import math

app = Flask(__name__)
app.config.from_object(Config)
Session(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    return mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB']
    )

def create_upload_folder():
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'static/uploads'), exist_ok=True)

# Call once at startup so folder exists (works with Flask 2.3+)
create_upload_folder()

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlmb/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

LANGUAGES = {
    'en': {
        'Home': 'Home',
        'Products': 'Products',
        'Login': 'Login',
        'Register User': 'Register User',
        'Register Farmer': 'Register Farmer',
        'Logout': 'Logout',
        'Dashboard': 'Dashboard',
        'Profile': 'Profile',
        'Admin': 'Admin',
        'Language': 'Language',
        'Browse Products': 'Browse Products',
        'Fresh produce directly from farmers': 'Fresh produce directly from farmers',
        'Support line': 'Shop seasonal fruits and vegetables harvested by local farmers. Support sustainable agriculture and enjoy premium quality.',
        'Quality Produce': 'Quality Produce',
        'Local Farmers': 'Local Farmers',
        'Seasonal Variety': 'Seasonal Variety',
        'Order Now': 'Order Now'
    },
    'mr': {
        'Home': 'मुख्यपृष्ठ',
        'Products': 'उत्पादने',
        'Login': 'लॉगिन',
        'Register User': 'वापरकर्ता नोंदणी',
        'Register Farmer': 'शेतकरी नोंदणी',
        'Logout': 'बाहेर पडा',
        'Dashboard': 'डॅशबोर्ड',
        'Profile': 'प्रोफाइल',
        'Admin': 'प्रशासक',
        'Language': 'भाषा',
        'Browse Products': 'उत्पादने पाहा',
        'Fresh produce directly from farmers': 'शेतकऱ्यांकडून थेट ताजी उत्पादने',
        'Support line': 'स्थानिक शेतकऱ्यांकडून हंगामी फळे व भाज्या. शाश्वत शेतीला समर्थन द्या आणि उत्कृष्ट गुणवत्ता मिळवा.',
        'Quality Produce': 'उत्तम दर्जाची उत्पादने',
        'Local Farmers': 'स्थानिक शेतकरी',
        'Seasonal Variety': 'हंगामी विविधता',
        'Order Now': 'ऑर्डर करा'
    },
    'hi': {
        'Home': 'होम',
        'Products': 'उत्पाद',
        'Login': 'लॉगिन',
        'Register User': 'उपयोगकर्ता पंजीकरण',
        'Register Farmer': 'किसान पंजीकरण',
        'Logout': 'लॉगआउट',
        'Dashboard': 'डैशबोर्ड',
        'Profile': 'प्रोफ़ाइल',
        'Admin': 'प्रशासक',
        'Language': 'भाषा',
        'Browse Products': 'उत्पाद देखें',
        'Fresh produce directly from farmers': 'किसानों से सीधे ताज़ा उत्पाद',
        'Support line': 'स्थानीय किसानों से मौसमी फल और सब्जियाँ। सतत कृषि का समर्थन करें और उत्कृष्ट गुणवत्ता पाएँ।',
        'Quality Produce': 'उत्कृष्ट गुणवत्ता',
        'Local Farmers': 'स्थानीय किसान',
        'Seasonal Variety': 'मौसमी विविधता',
        'Order Now': 'ऑर्डर करें'
    },
    'pa': {},
    'gu': {},
    'ta': {},
    'te': {},
    'kn': {},
    'bn': {},
    'or': {},
    'ml': {},
    'as': {},
    'mai': {}
}

@app.context_processor
def inject_i18n():
    lang = session.get('lang', 'en')
    texts = LANGUAGES.get(lang, LANGUAGES['en'])
    def t(key):
        return texts.get(key, key)
    return dict(t=t, lang=lang)

@app.context_processor
def inject_cart():
    cart = session.get('cart', {})
    try:
        count = sum(int(q) for q in cart.values())
    except Exception:
        count = 0
    return dict(cart_count=count)

def login_required(role=None):
    def decorator(f):
        def wrapped(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please login first!', 'error')
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash('Access denied!', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        wrapped.__name__ = f.__name__
        return wrapped
    return decorator

@app.route('/set_lang/<lang>')
def set_lang(lang):
    if lang not in LANGUAGES:
        lang = 'en'
    session['lang'] = lang
    next_url = request.args.get('next') or request.referrer or url_for('index')
    return redirect(next_url)

@app.route('/')
def index():
    products = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT p.*, u.username as farmer_name FROM products p JOIN users u ON p.farmer_id = u.id ORDER BY p.created_at DESC")
        products = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception:
        flash('Database connection unavailable. Showing info only.', 'error')
    return render_template('index.html', products=products)


@app.route('/products')
def products():
    products = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT p.*, u.username as farmer_name FROM products p JOIN users u ON p.farmer_id = u.id ORDER BY p.created_at DESC")
        products = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception:
        flash('Database connection unavailable.', 'error')
    return render_template('products.html', products=products)

def _get_cart():
    cart = session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}
    return cart

@app.route('/cart')
@login_required('user')
def view_cart():
    cart = _get_cart()
    items = []
    total = 0.0
    if cart:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        ids = tuple(int(pid) for pid in cart.keys())
        placeholders = ','.join(['%s'] * len(ids))
        cur.execute(f"SELECT * FROM products WHERE id IN ({placeholders})", ids)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        for p in rows:
            qty = int(cart.get(str(p['id'])) or cart.get(p['id']) or 1)
            line_total = float(p['price']) * qty
            total += line_total
            items.append({'product': p, 'qty': qty, 'line_total': line_total})
    return render_template('cart.html', items=items, total=total)

@app.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required('user')
def cart_add(product_id):
    qty_raw = request.form.get('quantity', '1')
    try:
        qty = max(1, int(qty_raw))
    except Exception:
        qty = 1
    cart = _get_cart()
    current = int(cart.get(str(product_id), 0))
    cart[str(product_id)] = current + qty
    session['cart'] = cart
    flash('Added to cart', 'success')
    return redirect(request.referrer or url_for('products'))

@app.route('/cart/remove/<int:product_id>', methods=['POST'])
@login_required('user')
def cart_remove(product_id):
    cart = _get_cart()
    cart.pop(str(product_id), None)
    session['cart'] = cart
    flash('Removed from cart', 'success')
    return redirect(request.referrer or url_for('view_cart'))

@app.route('/cart/update', methods=['POST'])
@login_required('user')
def cart_update():
    ids = request.form.getlist('product_id[]')
    qtys = request.form.getlist('quantity[]')
    cart = {}
    for i, q in zip(ids, qtys):
        try:
            qv = max(1, int(q))
            cart[str(int(i))] = qv
        except Exception:
            continue
    session['cart'] = cart
    flash('Cart updated', 'success')
    return redirect(url_for('view_cart'))

@app.route('/cart/checkout', methods=['POST'])
@login_required('user')
def cart_checkout():
    cart = _get_cart()
    if not cart:
        flash('Cart is empty', 'error')
        return redirect(url_for('view_cart'))
    cust_lat = request.form.get('lat')
    cust_lng = request.form.get('lng')
    cust_lat = float(cust_lat) if cust_lat else None
    cust_lng = float(cust_lng) if cust_lng else None
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    for pid, qty in cart.items():
        try:
            cur.execute("SELECT p.price, p.farmer_id, f.lat as f_lat, f.lng as f_lng, IFNULL(f.delivery_radius_km, 20) as radius FROM products p JOIN farmers f ON p.farmer_id=f.id WHERE p.id = %s", (int(pid),))
            prod = cur.fetchone()
        except mysql.connector.Error:
            cur.execute("SELECT p.price, p.farmer_id FROM products p JOIN farmers f ON p.farmer_id=f.id WHERE p.id = %s", (int(pid),))
            base = cur.fetchone()
            if base:
                base['f_lat'] = None
                base['f_lng'] = None
                base['radius'] = 20
                prod = base
            else:
                prod = None
        if not prod:
            continue
        total = float(prod['price']) * int(qty)
        distance_km = None
        mode = None
        if cust_lat is not None and cust_lng is not None and prod['f_lat'] is not None and prod['f_lng'] is not None:
            distance_km = haversine(prod['f_lat'], prod['f_lng'], cust_lat, cust_lng)
            mode = 'free_delivery' if distance_km <= float(prod['radius']) else 'pickup_required'
        else:
            mode = 'pickup_required'
        try:
            cur.execute("""
                INSERT INTO orders (user_id, product_id, quantity, total_price, customer_lat, customer_lng, distance_km, delivery_mode) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (session['user_id'], int(pid), int(qty), total, cust_lat, cust_lng, distance_km, mode))
        except mysql.connector.Error:
            cur.execute("""
                INSERT INTO orders (user_id, product_id, quantity, total_price) 
                VALUES (%s, %s, %s, %s)
            """, (session['user_id'], int(pid), int(qty), total))
        conn.commit()
    cur.close()
    conn.close()
    session['cart'] = {}
    flash('Order placed for all cart items', 'success')
    return redirect(url_for('user_profile'))
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if user and check_password_hash(user['password_hash'], password):
            try:
                up = conn.cursor()
                up.execute("UPDATE users SET last_login = NOW() WHERE id=%s", (user['id'],))
                conn.commit()
                up.close()
            except Exception:
                pass
        cursor.close()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Logged in successfully!', 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'farmer':
                return redirect(url_for('farmer_dashboard'))
            else:
                return redirect(url_for('user_profile'))
        flash('Invalid credentials!', 'error')
    return render_template('login.html')

@app.route('/register/user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, 'user')",
                           (username, email, password))
            conn.commit()
            flash('Registered successfully! Please login.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash('Username or email already exists!', 'error')
        finally:
            cursor.close()
            conn.close()
    return render_template('register_user.html')

@app.route('/register/farmer', methods=['GET', 'POST'])
def register_farmer():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Create farmer as a normal user with role='farmer'
            cursor.execute("INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, 'farmer')",
                           (username, email, password))
            user_id = cursor.lastrowid

            # Also create entry in farmers table so foreign keys work
            cursor.execute(
                "INSERT INTO farmers (id, name, email, address, phone, approved) VALUES (%s, %s, %s, %s, %s, %s)",
                (user_id, username, email, None, None, 0)
            )

            conn.commit()
            flash('Registered as farmer! Please login.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash('Username or email already exists!', 'error')
        finally:
            cursor.close()
            conn.close()
    return render_template('register_farmer.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/farmer/dashboard')
@login_required('farmer')
def farmer_dashboard():
    return render_template('farmer_dashboard.html')

@app.route('/farmer/products')
@login_required('farmer')
def farmer_products():
    user_id = session['user_id']
    products = {}
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        # First, fetch farmer products with location (robust to schema)
        try:
            cur.execute("""
                SELECT p.*, f.lat AS f_lat, f.lng AS f_lng
                FROM products p
                JOIN farmers f ON p.farmer_id = f.id
                WHERE p.farmer_id = %s
                ORDER BY p.created_at DESC
            """, (user_id,))
        except mysql.connector.Error:
            cur.execute("""
                SELECT p.*
                FROM products p
                WHERE p.farmer_id = %s
                ORDER BY p.created_at DESC
            """, (user_id,))
        prod_rows = cur.fetchall()
        for row in prod_rows:
            pid = row.get('id')
            if pid is None:
                continue
            products[pid] = row
            products[pid]['orders'] = []
            # ensure f_lat/f_lng keys exist for template even if null
            products[pid]['f_lat'] = products[pid].get('f_lat')
            products[pid]['f_lng'] = products[pid].get('f_lng')
        # Then, fetch orders in a separate step (optional fields guarded)
        if products:
            product_ids = tuple(products.keys())
            # Build IN clause safely
            placeholders = ','.join(['%s'] * len(product_ids))
            try:
                cur.execute(f"""
                    SELECT o.id AS order_id, o.user_id, o.product_id, o.quantity, o.status,
                           o.customer_lat, o.customer_lng, o.distance_km, o.delivery_mode,
                           u.username AS order_username
                    FROM orders o
                    LEFT JOIN users u ON o.user_id = u.id
                    WHERE o.product_id IN ({placeholders})
                    ORDER BY o.order_date DESC
                """, product_ids)
            except mysql.connector.Error:
                cur.execute(f"""
                    SELECT o.id AS order_id, o.user_id, o.product_id, o.quantity, o.status,
                           u.username AS order_username
                    FROM orders o
                    LEFT JOIN users u ON o.user_id = u.id
                    WHERE o.product_id IN ({placeholders})
                    ORDER BY o.id DESC
                """, product_ids)
            order_rows = cur.fetchall()
            for o in order_rows:
                pid = o.get('product_id')
                if pid in products:
                    products[pid]['orders'].append({
                        'order_id': o.get('order_id'),
                        'user_id': o.get('user_id'),
                        'username': o.get('order_username'),
                        'quantity': o.get('quantity'),
                        'status': o.get('status'),
                        'customer_lat': o.get('customer_lat'),
                        'customer_lng': o.get('customer_lng'),
                        'distance_km': o.get('distance_km'),
                        'delivery_mode': o.get('delivery_mode')
                    })
        cur.close()
    except Exception:
        # Silent fallback: show empty list without error flash
        products = {}
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
    return render_template('farmer_products.html', products=list(products.values()))

@app.route('/farmer/add_product', methods=['GET', 'POST'])
@login_required('farmer')
def add_product():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        description = request.form.get('description','').strip()
        try:
            price = float(request.form.get('price',''))
            stock = int(request.form.get('stock',''))
        except Exception:
            flash('Invalid price or stock value', 'error')
            return render_template('add_product.html')
        if price < 0 or stock < 0:
            flash('Price and stock must be non-negative', 'error')
            return render_template('add_product.html')
        image = request.files.get('image')
        image_path = None
        if image:
            if not allowed_file(image.filename):
                flash('Unsupported image type', 'error')
                return render_template('add_product.html')
            filename = secure_filename(image.filename)
            ext = os.path.splitext(filename)[1]
            filename = f"{session['user_id']}_{int(time.time())}{ext}"
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename).replace('\\','/')
            image.save(image_path)
            try:
                img = Image.open(image_path)
                img.thumbnail((400, 400))
                img.save(image_path)
            except Exception:
                flash('Failed to process image', 'error')
                return render_template('add_product.html')
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            check = conn.cursor(dictionary=True)
            check.execute("SELECT id FROM farmers WHERE id=%s", (session['user_id'],))
            frow = check.fetchone()
            if not frow:
                check.execute("SELECT username, email FROM users WHERE id=%s", (session['user_id'],))
                u = check.fetchone()
                if u:
                    check.execute("INSERT INTO farmers (id, name, email, approved) VALUES (%s, %s, %s, %s)",
                                  (session['user_id'], u['username'], u['email'], 0))
                    conn.commit()
            check.close()
            cursor.execute("INSERT INTO products (farmer_id, name, description, price, image, stock) VALUES (%s, %s, %s, %s, %s, %s)",
                           (session['user_id'], name, description, price, image_path, stock))
            conn.commit()
            flash('Product added!', 'success')
        except mysql.connector.Error as e:
            flash('Failed to add product', 'error')
            return render_template('add_product.html')
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('farmer_products'))
    return render_template('add_product.html')

@app.route('/farmer/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required('farmer')
def edit_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products WHERE id = %s AND farmer_id = %s", (product_id, session['user_id']))
    product = cursor.fetchone()
    if not product:
        flash('Product not found!', 'error')
        return redirect(url_for('farmer_products'))
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        image_path = product['image']
        image = request.files.get('image')
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename).replace('\\','/')
            image.save(image_path)
            img = Image.open(image_path)
            img.thumbnail((400, 400))
            img.save(image_path)
        cursor.execute("""
            UPDATE products SET name=%s, description=%s, price=%s, stock=%s, image=%s 
            WHERE id=%s
        """, (name, description, price, stock, image_path, product_id))
        conn.commit()
        flash('Product updated!', 'success')
        return redirect(url_for('farmer_products'))
    cursor.close()
    conn.close()
    return render_template('edit_product.html', product=product)

@app.route('/farmer/delete_product/<int:product_id>')
@login_required('farmer')
def delete_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = %s AND farmer_id = %s", (product_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Product deleted!', 'success')
    return redirect(url_for('farmer_products'))

@app.route('/order/<int:product_id>', methods=['POST'])
@login_required('user')
def place_order(product_id):
    try:
        quantity = int(request.form.get('quantity', '1'))
    except Exception:
        quantity = 1
    cust_lat = request.form.get('lat')
    cust_lng = request.form.get('lng')
    cust_lat = float(cust_lat) if cust_lat else None
    cust_lng = float(cust_lng) if cust_lng else None
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    prod = None
    try:
        cursor.execute("SELECT p.price, p.farmer_id, f.lat as f_lat, f.lng as f_lng, IFNULL(f.delivery_radius_km, 20) as radius FROM products p JOIN farmers f ON p.farmer_id=f.id WHERE p.id = %s", (product_id,))
        prod = cursor.fetchone()
    except mysql.connector.Error:
        cursor.execute("SELECT p.price, p.farmer_id FROM products p JOIN farmers f ON p.farmer_id=f.id WHERE p.id = %s", (product_id,))
        base = cursor.fetchone()
        if base:
            base['f_lat'] = None
            base['f_lng'] = None
            base['radius'] = 20
            prod = base
    if prod:
        total = float(prod['price']) * quantity
        distance_km = None
        mode = None
        if cust_lat is not None and cust_lng is not None and prod['f_lat'] is not None and prod['f_lng'] is not None:
            distance_km = haversine(prod['f_lat'], prod['f_lng'], cust_lat, cust_lng)
            mode = 'free_delivery' if distance_km <= float(prod['radius']) else 'pickup_required'
        else:
            mode = 'pickup_required'
        try:
            cursor.execute("""
                INSERT INTO orders (user_id, product_id, quantity, total_price, customer_lat, customer_lng, distance_km, delivery_mode) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (session['user_id'], product_id, quantity, total, cust_lat, cust_lng, distance_km, mode))
        except mysql.connector.Error:
            cursor.execute("""
                INSERT INTO orders (user_id, product_id, quantity, total_price) 
                VALUES (%s, %s, %s, %s)
            """, (session['user_id'], product_id, quantity, total))
        conn.commit()
        if distance_km is not None:
            flash(f'Your order has been received. Your distance from the farmer: {distance_km:.2f} KM.', 'success')
        else:
            flash('Your order has been received.', 'success')
    else:
        flash('Product not found or unavailable.', 'error')
    cursor.close()
    conn.close()
    return redirect(url_for('user_profile'))

@app.route('/order/cancel/<int:order_id>', methods=['POST'])
@login_required('user')
def cancel_order(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE orders SET status=%s WHERE id=%s AND user_id=%s AND (status IS NULL OR status NOT IN ('cancelled','delivered'))",
            ('cancelled', order_id, session['user_id'])
        )
        if cursor.rowcount == 0:
            try:
                cursor.execute("DELETE FROM orders WHERE id=%s AND user_id=%s", (order_id, session['user_id']))
                conn.commit()
                flash('Order removed.', 'success')
                cursor.close()
                conn.close()
                return redirect(url_for('user_profile'))
            except mysql.connector.Error:
                flash('Unable to cancel this order.', 'error')
        else:
            conn.commit()
            flash('Order cancelled.', 'success')
    except mysql.connector.Error:
        try:
            cursor.execute("DELETE FROM orders WHERE id=%s AND user_id=%s", (order_id, session['user_id']))
            conn.commit()
            flash('Order removed.', 'success')
        except mysql.connector.Error:
            flash('Unable to cancel this order.', 'error')
    cursor.close()
    conn.close()
    return redirect(url_for('user_profile'))

@app.route('/user/profile')
@login_required('user')
def user_profile():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT o.*, p.name as product_name, p.image, f.username as farmer_name 
        FROM orders o 
        JOIN products p ON o.product_id = p.id 
        JOIN users f ON p.farmer_id = f.id 
        WHERE o.user_id = %s 
        ORDER BY o.order_date DESC
    """, (user_id,))
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('user_profile.html', orders=orders)

@app.route('/admin/dashboard')
@login_required('admin')
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE role = 'user' ORDER BY created_at DESC")
    users = cursor.fetchall()
    cursor.execute("SELECT * FROM users WHERE role = 'farmer' ORDER BY created_at DESC")
    farmers = cursor.fetchall()
    cursor.execute("SELECT p.*, u.username as farmer FROM products p JOIN users u ON p.farmer_id = u.id ORDER BY p.created_at DESC")
    products = cursor.fetchall()
    cursor.execute("""
        SELECT o.*, u.username as user_name, p.name as product_name, f.username as farmer_name 
        FROM orders o 
        JOIN users u ON o.user_id = u.id 
        JOIN products p ON o.product_id = p.id 
        JOIN users f ON p.farmer_id = f.id 
        ORDER BY o.order_date DESC
    """)
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin_dashboard.html', users=users, farmers=farmers, products=products, orders=orders)

# keep routes below; app is run via run.py
# OWNER LOGIN
@app.route('/owner/login', methods=['GET','POST'])
def owner_login():
    if request.method=='POST':
        email=request.form.get('email')
        pwd=request.form.get('password')
        owner_email = app.config.get('OWNER_EMAIL')
        owner_password = app.config.get('OWNER_PASSWORD')
        if owner_email and owner_password and email==owner_email and pwd==owner_password:
            session['owner']=True
            return redirect('/owner/dashboard')
        return "Invalid Owner Credentials"
    return render_template('owner_login.html')

@app.route('/owner/dashboard')
def owner_dashboard():
    if not session.get('owner'):
        return redirect('/owner/login')
    conn = get_db_connection()
    cur = conn.cursor()
    # fetch users, farmers, products
    try:
        cur.execute("SELECT * FROM users WHERE last_login IS NOT NULL ORDER BY last_login DESC")
        users = cur.fetchall()
    except:
        users = []
    try:
        cur.execute("SELECT f.* FROM farmers f JOIN users u ON f.id=u.id WHERE u.last_login IS NOT NULL AND u.role='farmer' ORDER BY u.last_login DESC")
        farmers = cur.fetchall()
    except:
        farmers = []
    try:
        cur.execute("SELECT * FROM products")
        products = cur.fetchall()
    except:
        products = []

    # analytics: orders count, revenue sum, monthly orders (best-effort)
    try:
        cur.execute("SELECT COUNT(*) FROM orders")
        orders_count = cur.fetchone()[0]
    except:
        orders_count = 0
    try:
        cur.execute("SELECT IFNULL(SUM(total_price),0) FROM orders")
        revenue = cur.fetchone()[0]
    except:
        revenue = 0

    # monthly orders - attempt: group by MONTH(date) if date column exists
    monthly_labels = []
    monthly_values = []
    try:
        cur.execute("""SELECT DATE_FORMAT(order_date, '%%Y-%%m') as ym, COUNT(*) as cnt
                       FROM orders
                       GROUP BY ym
                       ORDER BY ym DESC
                       LIMIT 12""")
        rows = cur.fetchall()
        rows = rows[::-1]  # oldest first
        monthly_labels = [r[0] for r in rows]
        monthly_values = [r[1] for r in rows]
    except:
        monthly_labels = []
        monthly_values = []

    # prepare json-able data
    import json
    orders_json = orders_count
    revenue_json = float(revenue) if revenue is not None else 0
    monthly_labels_json = json.dumps(monthly_labels)
    monthly_values_json = json.dumps(monthly_values)

    return render_template('owner_dashboard.html',
                           users=users, farmers=farmers, products=products,
                           orders_json=orders_json, revenue_json=revenue_json,
                           monthly_labels=monthly_labels, monthly_values=monthly_values)




# --------- OWNER MANAGEMENT ROUTES ----------
@app.route('/owner/delete/user/<int:uid>', methods=['POST'])
def owner_delete_user(uid):
    if not session.get('owner'):
        return redirect('/owner/login')
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM users WHERE id=%s", (uid,))
        conn.commit()
        return redirect('/owner/dashboard')
    except Exception as e:
        return str(e)

@app.route('/owner/delete/farmer/<int:fid>', methods=['POST'])
def owner_delete_farmer(fid):
    if not session.get('owner'):
        return redirect('/owner/login')
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM farmers WHERE id=%s", (fid,))
        conn.commit()
        return redirect('/owner/dashboard')
    except Exception as e:
        return str(e)

@app.route('/owner/delete/product/<int:pid>', methods=['POST'])
def owner_delete_product(pid):
    if not session.get('owner'):
        return redirect('/owner/login')
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM products WHERE id=%s", (pid,))
        conn.commit()
        return redirect('/owner/dashboard')
    except Exception as e:
        return str(e)

@app.route('/owner/approve/farmer/<int:fid>', methods=['POST'])
def owner_approve_farmer(fid):
    if not session.get('owner'):
        return redirect('/owner/login')
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # assumes farmers table has 'approved' column (0/1)
        cur.execute("UPDATE farmers SET approved=1 WHERE id=%s", (fid,))
        conn.commit()
        return redirect('/owner/dashboard')
    except Exception as e:
        return str(e)

@app.route('/owner/reject/farmer/<int:fid>', methods=['POST'])
def owner_reject_farmer(fid):
    if not session.get('owner'):
        return redirect('/owner/login')
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE farmers SET approved=0 WHERE id=%s", (fid,))
        conn.commit()
        return redirect('/owner/dashboard')
    except Exception as e:
        return str(e)

@app.route('/owner/reset_password/user/<int:uid>', methods=['POST'])
def owner_reset_password(uid):
    if not session.get('owner'):
        return redirect('/owner/login')
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        new_hash = generate_password_hash('password123')
        cur.execute("UPDATE users SET password_hash=%s WHERE id=%s", (new_hash, uid))
        conn.commit()
        return redirect('/owner/dashboard')
    except Exception as e:
        return str(e)
# ---------------------------------------------
