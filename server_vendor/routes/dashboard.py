"""Vendor dashboard - orders, analytics, pricing management."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from flask import Blueprint, request, jsonify, session
from db import get_db
from werkzeug.utils import secure_filename
import time

dashboard_bp = Blueprint('dashboard', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', '..', 'server_user', 'static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def handle_upload():
    if 'image' not in request.files:
        return None
    file = request.files['image']
    if file.filename == '':
        return None
    filename = secure_filename(file.filename)
    unique_name = f"{int(time.time())}_{filename}"
    file.save(os.path.join(UPLOAD_FOLDER, unique_name))
    # We store the relative path that the user server (port 3000) can serve
    return f"/static/uploads/{unique_name}"

def require_vendor():
    if 'user_id' not in session or session.get('role') != 'vendor':
        return None
    return session['user_id']

# ─── MY SERVICES ──────────────────────────────────────────────────────────────
@dashboard_bp.route('/vendor/services', methods=['GET'])
def my_services():
    vendor_id = require_vendor()
    if not vendor_id:
        return jsonify({'error': 'Not authenticated'}), 401

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # Get vendor's designated service type
        cursor.execute("SELECT vendor_service_type FROM users WHERE id=%s", (vendor_id,))
        user = cursor.fetchone()
        service_type = user['vendor_service_type'] if user else None

        halls = []
        catering = []
        cars = []
        photography = []
        decorations = []

        if service_type == 'hall':
            cursor.execute("SELECT * FROM halls WHERE vendor_id=%s", (vendor_id,))
            halls = cursor.fetchall()
        elif service_type == 'catering':
            cursor.execute("SELECT * FROM catering_companies WHERE user_id=%s", (vendor_id,))
            catering = cursor.fetchall()
        elif service_type == 'luxury_car':
            cursor.execute("SELECT * FROM luxury_cars WHERE user_id=%s", (vendor_id,))
            cars = cursor.fetchall()
        elif service_type == 'photography':
            cursor.execute("SELECT * FROM photography_services WHERE user_id=%s", (vendor_id,))
            photography = cursor.fetchall()
        elif service_type == 'decoration':
            cursor.execute("SELECT * FROM decorations WHERE user_id=%s", (vendor_id,))
            decorations = cursor.fetchall()

        return jsonify({
            'service_type': service_type,
            'halls': halls,
            'catering': catering,
            'cars': cars,
            'photography': photography,
            'decorations': decorations
        })
    finally:
        cursor.close(); conn.close()

# ─── MY ORDERS ────────────────────────────────────────────────────────────────
@dashboard_bp.route('/vendor/orders', methods=['GET'])
def my_orders():
    vendor_id = require_vendor()
    if not vendor_id:
        return jsonify({'error': 'Not authenticated'}), 401

    status_filter = request.args.get('status', '')
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # Fetch all bookings related to this vendor's services
        sql = """
            SELECT b.*, u.name as customer_name, u.phone as customer_phone, u.email as customer_email,
                CASE b.service_type
                    WHEN 'hall' THEN (SELECT name FROM halls WHERE id=b.service_id)
                    WHEN 'catering' THEN (SELECT company_name FROM catering_companies WHERE id=b.service_id)
                    WHEN 'luxury_car' THEN (SELECT CONCAT(car_name,' ',car_model) FROM luxury_cars WHERE id=b.service_id)
                    WHEN 'photography' THEN (SELECT service_name FROM photography_services WHERE id=b.service_id)
                    WHEN 'decorations' THEN (SELECT theme_name FROM decorations WHERE id=b.service_id)
                END as service_name
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            WHERE (
                (b.service_type='hall' AND b.service_id IN (SELECT id FROM halls WHERE vendor_id=%s)) OR
                (b.service_type='catering' AND b.service_id IN (SELECT id FROM catering_companies WHERE user_id=%s)) OR
                (b.service_type='luxury_car' AND b.service_id IN (SELECT id FROM luxury_cars WHERE user_id=%s)) OR
                (b.service_type='photography' AND b.service_id IN (SELECT id FROM photography_services WHERE user_id=%s)) OR
                (b.service_type='decorations' AND b.service_id IN (SELECT id FROM decorations WHERE user_id=%s))
            )
        """
        params = [vendor_id]*5
        if status_filter:
            sql += " AND b.status=%s"
            params.append(status_filter)
        sql += " ORDER BY b.created_at DESC"
        cursor.execute(sql, params)
        orders = cursor.fetchall()
        for o in orders:
            for k, v in o.items():
                if hasattr(v, 'isoformat'):
                    o[k] = v.isoformat()
        return jsonify(orders)
    finally:
        cursor.close(); conn.close()

@dashboard_bp.route('/vendor/orders/<int:booking_id>/status', methods=['PUT'])
def update_order_status(booking_id):
    vendor_id = require_vendor()
    if not vendor_id:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json()
    new_status = data.get('status')
    if new_status not in ('confirmed', 'completed', 'cancelled'):
        return jsonify({'error': 'Invalid status'}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        # Verify this booking belongs to vendor
        cursor.execute("""
            SELECT id FROM bookings WHERE id=%s AND (
                (service_type='hall' AND service_id IN (SELECT id FROM halls WHERE vendor_id=%s)) OR
                (service_type='catering' AND service_id IN (SELECT id FROM catering_companies WHERE user_id=%s)) OR
                (service_type='luxury_car' AND service_id IN (SELECT id FROM luxury_cars WHERE user_id=%s)) OR
                (service_type='photography' AND service_id IN (SELECT id FROM photography_services WHERE user_id=%s)) OR
                (service_type='decorations' AND service_id IN (SELECT id FROM decorations WHERE user_id=%s))
            )
        """, [booking_id] + [vendor_id]*5)
        if not cursor.fetchone():
            return jsonify({'error': 'Booking not found or unauthorized'}), 404
        cursor.execute("UPDATE bookings SET status=%s WHERE id=%s", (new_status, booking_id))
        conn.commit()
        return jsonify({'message': f'Order status updated to {new_status}'})
    finally:
        cursor.close(); conn.close()

# ─── ANALYTICS ────────────────────────────────────────────────────────────────
@dashboard_bp.route('/vendor/analytics', methods=['GET'])
def analytics():
    vendor_id = require_vendor()
    if not vendor_id:
        return jsonify({'error': 'Not authenticated'}), 401

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # Bookings by status
        cursor.execute("""
            SELECT b.status, COUNT(*) as count, COALESCE(SUM(b.total_amount),0) as total_revenue
            FROM bookings b
            WHERE (
                (b.service_type='hall' AND b.service_id IN (SELECT id FROM halls WHERE vendor_id=%s)) OR
                (b.service_type='catering' AND b.service_id IN (SELECT id FROM catering_companies WHERE user_id=%s)) OR
                (b.service_type='luxury_car' AND b.service_id IN (SELECT id FROM luxury_cars WHERE user_id=%s)) OR
                (b.service_type='photography' AND b.service_id IN (SELECT id FROM photography_services WHERE user_id=%s)) OR
                (b.service_type='decorations' AND b.service_id IN (SELECT id FROM decorations WHERE user_id=%s))
            )
            GROUP BY b.status
        """, [vendor_id]*5)
        by_status = cursor.fetchall()

        # Bookings over last 30 days
        cursor.execute("""
            SELECT DATE(b.created_at) as day, COUNT(*) as count
            FROM bookings b
            WHERE b.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            AND (
                (b.service_type='hall' AND b.service_id IN (SELECT id FROM halls WHERE vendor_id=%s)) OR
                (b.service_type='catering' AND b.service_id IN (SELECT id FROM catering_companies WHERE user_id=%s)) OR
                (b.service_type='luxury_car' AND b.service_id IN (SELECT id FROM luxury_cars WHERE user_id=%s)) OR
                (b.service_type='photography' AND b.service_id IN (SELECT id FROM photography_services WHERE user_id=%s)) OR
                (b.service_type='decorations' AND b.service_id IN (SELECT id FROM decorations WHERE user_id=%s))
            )
            GROUP BY DATE(b.created_at) ORDER BY day
        """, [vendor_id]*5)
        over_time = cursor.fetchall()
        for r in over_time:
            if hasattr(r.get('day'), 'isoformat'):
                r['day'] = r['day'].isoformat()

        # By service type
        cursor.execute("""
            SELECT b.service_type, COUNT(*) as count
            FROM bookings b
            WHERE (
                (b.service_type='hall' AND b.service_id IN (SELECT id FROM halls WHERE vendor_id=%s)) OR
                (b.service_type='catering' AND b.service_id IN (SELECT id FROM catering_companies WHERE user_id=%s)) OR
                (b.service_type='luxury_car' AND b.service_id IN (SELECT id FROM luxury_cars WHERE user_id=%s)) OR
                (b.service_type='photography' AND b.service_id IN (SELECT id FROM photography_services WHERE user_id=%s)) OR
                (b.service_type='decorations' AND b.service_id IN (SELECT id FROM decorations WHERE user_id=%s))
            )
            GROUP BY b.service_type
        """, [vendor_id]*5)
        by_type = cursor.fetchall()

        return jsonify({'by_status': by_status, 'over_time': over_time, 'by_type': by_type})
    finally:
        cursor.close(); conn.close()

# ─── SERVICE MANAGEMENT (Generic) ──────────────────────────────────────────────
def check_can_add(vendor_id, table_name, user_col='vendor_id'):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {user_col}=%s", (vendor_id,))
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count == 0

def get_vendor_service_type(vendor_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT vendor_service_type FROM users WHERE id=%s", (vendor_id,))
    res = cursor.fetchone()
    cursor.close(); conn.close()
    return res['vendor_service_type'] if res else None

# HALLS
@dashboard_bp.route('/vendor/hall', methods=['POST'])
def add_hall():
    v_id = require_vendor()
    if not v_id: return jsonify({'error': 'Unauthorized'}), 401
    if get_vendor_service_type(v_id) != 'hall': return jsonify({'error': 'You are not a Hall vendor'}), 403
    
    image_url = handle_upload() or request.form.get('image_url')
    location_url = request.form.get('location_url')
    
    conn = get_db(); cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO halls (name,city,capacity,amenities,price_per_night,address,image_url,location_url,vendor_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (request.form.get('name'), request.form.get('city'), request.form.get('capacity'), request.form.get('amenities',''), request.form.get('price_per_night'), request.form.get('address'), image_url, location_url, v_id))
        conn.commit()
        return jsonify({'message': 'Hall added', 'image_url': image_url}), 201
    finally: cursor.close(); conn.close()

@dashboard_bp.route('/vendor/hall/<int:id>', methods=['DELETE'])
def delete_hall(id):
    v_id = require_vendor()
    if not v_id: return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("DELETE FROM halls WHERE id=%s AND vendor_id=%s", (id, v_id))
    conn.commit()
    cursor.close(); conn.close()
    return jsonify({'message': 'Hall removed'})

@dashboard_bp.route('/vendor/hall/<int:sid>', methods=['PUT'])
def update_hall(sid):
    v_id = require_vendor()
    if not v_id: return jsonify({'error': 'Unauthorized'}), 401
    
    image_url = handle_upload() or request.form.get('image_url')
    location_url = request.form.get('location_url')
    
    conn = get_db(); cursor = conn.cursor()
    try:
        sql = "UPDATE halls SET name=%s, city=%s, capacity=%s, amenities=%s, price_per_night=%s, address=%s, location_url=%s"
        params = [request.form.get('name'), request.form.get('city'), request.form.get('capacity'), request.form.get('amenities',''), request.form.get('price_per_night'), request.form.get('address'), location_url]
        if image_url:
            sql += ", image_url=%s"
            params.append(image_url)
        sql += " WHERE id=%s AND vendor_id=%s"
        params += [sid, v_id]
        cursor.execute(sql, params)
        conn.commit()
        return jsonify({'message': 'Hall updated'})
    finally: cursor.close(); conn.close()

# CATERING
@dashboard_bp.route('/vendor/catering', methods=['POST'])
def add_catering():
    v_id = require_vendor()
    if not v_id: return jsonify({'error': 'Unauthorized'}), 401
    if get_vendor_service_type(v_id) != 'catering': return jsonify({'error': 'You are not a Catering vendor'}), 403

    image_url = handle_upload() or request.form.get('image_url')
    location_url = request.form.get('location_url')

    conn = get_db(); cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO catering_companies (user_id, company_name, city, price_per_plate, image_url, location_url) VALUES (%s,%s,%s,%s,%s,%s)",
            (v_id, request.form.get('company_name'), request.form.get('city'), request.form.get('price_per_plate'), image_url, location_url))
        conn.commit()
        return jsonify({'message': 'Catering company added', 'image_url': image_url}), 201
    finally: cursor.close(); conn.close()

@dashboard_bp.route('/vendor/catering/<int:id>', methods=['DELETE'])
def delete_catering(id):
    v_id = require_vendor()
    if not v_id: return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("DELETE FROM catering_companies WHERE id=%s AND user_id=%s", (id, v_id))
    conn.commit()
    cursor.close(); conn.close()
    return jsonify({'message': 'Removed'})

@dashboard_bp.route('/vendor/catering/<int:sid>', methods=['PUT'])
def update_catering(sid):
    v_id = require_vendor()
    if not v_id: return jsonify({'error': 'Unauthorized'}), 401
    image_url = handle_upload() or request.form.get('image_url')
    location_url = request.form.get('location_url')
    conn = get_db(); cursor = conn.cursor()
    try:
        sql = "UPDATE catering_companies SET company_name=%s, city=%s, price_per_plate=%s, location_url=%s"
        params = [request.form.get('company_name'), request.form.get('city'), request.form.get('price_per_plate'), location_url]
        if image_url:
            sql += ", image_url=%s"
            params.append(image_url)
        sql += " WHERE id=%s AND user_id=%s"
        params += [sid, v_id]
        cursor.execute(sql, params)
        conn.commit()
        return jsonify({'message': 'Catering updated'})
    finally: cursor.close(); conn.close()

# CARS
@dashboard_bp.route('/vendor/luxury_car', methods=['POST'])
def add_car():
    v_id = require_vendor()
    if not v_id: return jsonify({'error': 'Unauthorized'}), 401
    if get_vendor_service_type(v_id) != 'luxury_car': return jsonify({'error': 'You are not a Luxury Car vendor'}), 403

    image_url = handle_upload() or request.form.get('image_url')
    location_url = request.form.get('location_url')

    conn = get_db(); cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO luxury_cars (user_id, car_name, car_model, city, rate_per_km, per_day_rent, km_limit, per_hour_rent, image_url, location_url) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (v_id, request.form.get('car_name'), request.form.get('car_model'), request.form.get('city'), request.form.get('rate_per_km'), request.form.get('per_day_rent', 0), request.form.get('km_limit', 0), request.form.get('per_hour_rent', 0), image_url, location_url))
        conn.commit()
        return jsonify({'message': 'Car added', 'image_url': image_url}), 201
    finally: cursor.close(); conn.close()

@dashboard_bp.route('/vendor/luxury_car/<int:id>', methods=['DELETE'])
def delete_car(id):
    v_id = require_vendor()
    if not v_id: return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("DELETE FROM luxury_cars WHERE id=%s AND user_id=%s", (id, v_id))
    conn.commit()
    cursor.close(); conn.close()
    return jsonify({'message': 'Removed'})

@dashboard_bp.route('/vendor/luxury_car/<int:sid>', methods=['PUT'])
def update_car(sid):
    v_id = require_vendor()
    if not v_id: return jsonify({'error': 'Unauthorized'}), 401
    image_url = handle_upload() or request.form.get('image_url')
    location_url = request.form.get('location_url')
    conn = get_db(); cursor = conn.cursor()
    try:
        sql = "UPDATE luxury_cars SET car_name=%s, car_model=%s, city=%s, rate_per_km=%s, per_day_rent=%s, km_limit=%s, per_hour_rent=%s, location_url=%s"
        params = [request.form.get('car_name'), request.form.get('car_model'), request.form.get('city'), request.form.get('rate_per_km'), request.form.get('per_day_rent', 0), request.form.get('km_limit', 0), request.form.get('per_hour_rent', 0), location_url]
        if image_url:
            sql += ", image_url=%s"
            params.append(image_url)
        sql += " WHERE id=%s AND user_id=%s"
        params += [sid, v_id]
        cursor.execute(sql, params)
        conn.commit()
        return jsonify({'message': 'Car updated'})
    finally: cursor.close(); conn.close()

# PHOTOGRAPHY
@dashboard_bp.route('/vendor/photography', methods=['POST'])
def add_photo():
    v_id = require_vendor()
    if not v_id: return jsonify({'error': 'Unauthorized'}), 401
    if get_vendor_service_type(v_id) != 'photography': return jsonify({'error': 'You are not a Photography vendor'}), 403

    image_url = handle_upload() or request.form.get('image_url')
    location_url = request.form.get('location_url')

    conn = get_db(); cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO photography_services (user_id, service_name, city, base_price, price_per_hour, image_url, location_url) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (v_id, request.form.get('service_name'), request.form.get('city'), request.form.get('base_price'), request.form.get('price_per_hour'), image_url, location_url))
        conn.commit()
        return jsonify({'message': 'Service added', 'image_url': image_url}), 201
    finally: cursor.close(); conn.close()

@dashboard_bp.route('/vendor/photography/<int:id>', methods=['DELETE'])
def delete_photo(id):
    v_id = require_vendor()
    if not v_id: return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("DELETE FROM photography_services WHERE id=%s AND user_id=%s", (id, v_id))
    conn.commit()
    cursor.close(); conn.close()
    return jsonify({'message': 'Removed'})

@dashboard_bp.route('/vendor/photography/<int:sid>', methods=['PUT'])
def update_photo(sid):
    v_id = require_vendor()
    if not v_id: return jsonify({'error': 'Unauthorized'}), 401
    image_url = handle_upload() or request.form.get('image_url')
    location_url = request.form.get('location_url')
    conn = get_db(); cursor = conn.cursor()
    try:
        sql = "UPDATE photography_services SET service_name=%s, city=%s, base_price=%s, price_per_hour=%s, location_url=%s"
        params = [request.form.get('service_name'), request.form.get('city'), request.form.get('base_price'), request.form.get('price_per_hour'), location_url]
        if image_url:
            sql += ", image_url=%s"
            params.append(image_url)
        sql += " WHERE id=%s AND user_id=%s"
        params += [sid, v_id]
        cursor.execute(sql, params)
        conn.commit()
        return jsonify({'message': 'Photography updated'})
    finally: cursor.close(); conn.close()

# DECORATIONS
@dashboard_bp.route('/vendor/decoration', methods=['POST'])
def add_decor():
    v_id = require_vendor()
    if not v_id: return jsonify({'error': 'Unauthorized'}), 401
    if get_vendor_service_type(v_id) != 'decoration': return jsonify({'error': 'You are not a Decoration vendor'}), 403

    image_url = handle_upload() or request.form.get('image_url')
    location_url = request.form.get('location_url')

    conn = get_db(); cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO decorations (user_id, theme_name, religion_style, culture_style, city, base_price, image_url, location_url) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (v_id, request.form.get('theme_name'), request.form.get('religion_style'), request.form.get('culture_style'), request.form.get('city'), request.form.get('base_price'), image_url, location_url))
        conn.commit()
        return jsonify({'message': 'Decoration added', 'image_url': image_url}), 201
    finally: cursor.close(); conn.close()

@dashboard_bp.route('/vendor/decoration/<int:id>', methods=['DELETE'])
def delete_decor(id):
    v_id = require_vendor()
    if not v_id: return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("DELETE FROM decorations WHERE id=%s AND user_id=%s", (id, v_id))
    conn.commit()
    cursor.close(); conn.close()
    return jsonify({'message': 'Removed'})

@dashboard_bp.route('/vendor/decoration/<int:sid>', methods=['PUT'])
def update_decor(sid):
    v_id = require_vendor()
    if not v_id: return jsonify({'error': 'Unauthorized'}), 401
    image_url = handle_upload() or request.form.get('image_url')
    location_url = request.form.get('location_url')
    conn = get_db(); cursor = conn.cursor()
    try:
        sql = "UPDATE decorations SET theme_name=%s, religion_style=%s, culture_style=%s, city=%s, base_price=%s, location_url=%s"
        params = [request.form.get('theme_name'), request.form.get('religion_style'), request.form.get('culture_style'), request.form.get('city'), request.form.get('base_price'), location_url]
        if image_url:
            sql += ", image_url=%s"
            params.append(image_url)
        sql += " WHERE id=%s AND user_id=%s"
        params += [sid, v_id]
        cursor.execute(sql, params)
        conn.commit()
        return jsonify({'message': 'Decoration updated'})
    finally: cursor.close(); conn.close()

# PRICE UPDATES
@dashboard_bp.route('/vendor/services/<string:stype>/<int:sid>/price', methods=['PUT'])
def update_price(stype, sid):
    v_id = require_vendor()
    if not v_id: return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    price = data.get('price')
    
    table_map = {
        'hall': ('halls', 'price_per_night', 'vendor_id'),
        'catering': ('catering_companies', 'price_per_plate', 'user_id'),
        'luxury_car': ('luxury_cars', 'rate_per_km', 'user_id'),
        'photography': ('photography_services', 'base_price', 'user_id'),
        'decoration': ('decorations', 'base_price', 'user_id')
    }
    if stype not in table_map: return jsonify({'error': 'Invalid service type'}), 400
    
    t, col, uid_col = table_map[stype]
    conn = get_db(); cursor = conn.cursor()
    cursor.execute(f"UPDATE {t} SET {col}=%s WHERE id=%s AND {uid_col}=%s", (price, sid, v_id))
    conn.commit()
    cursor.close(); conn.close()
    return jsonify({'message': 'Price updated'})

