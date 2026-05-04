"""Services/search routes for user server."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from flask import Blueprint, request, jsonify
from db import get_db

services_bp = Blueprint('services', __name__)

# ─── HALLS ────────────────────────────────────────────────────────────────────
@services_bp.route('/halls', methods=['GET'])
def list_halls():
    city = request.args.get('city', '')
    capacity = request.args.get('capacity', 0, type=int)
    max_price = request.args.get('max_price', 9999999, type=float)
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        sql = "SELECT h.*, u.name as vendor_name, u.phone as vendor_phone FROM halls h LEFT JOIN users u ON h.vendor_id=u.id WHERE h.status='approved'"
        params = []
        if city:
            sql += " AND (h.city LIKE %s OR h.city = 'All Cities in Tamilnadu')"
            params.append(f'%{city}%')
        if capacity:
            sql += " AND h.capacity >= %s"
            params.append(capacity)
        sql += " AND h.price_per_night <= %s ORDER BY h.price_per_night"
        params.append(max_price)
        cursor.execute(sql, params)
        halls = cursor.fetchall()
        for h in halls:
            if h.get('latitude'): h['latitude'] = float(h['latitude'])
            if h.get('longitude'): h['longitude'] = float(h['longitude'])
        return jsonify(halls)
    finally:
        cursor.close(); conn.close()

@services_bp.route('/halls/<int:hall_id>', methods=['GET'])
def get_hall(hall_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT h.*, u.name as vendor_name, u.phone as vendor_phone FROM halls h LEFT JOIN users u ON h.vendor_id=u.id WHERE h.id=%s", (hall_id,))
        hall = cursor.fetchone()
        return jsonify(hall) if hall else (jsonify({'error': 'Not found'}), 404)
    finally:
        cursor.close(); conn.close()

# ─── CATERING ─────────────────────────────────────────────────────────────────
@services_bp.route('/catering', methods=['GET'])
def list_catering():
    city = request.args.get('city', '')
    veg_type = request.args.get('type', '')
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        sql = "SELECT c.*, u.name as vendor_name FROM catering_companies c LEFT JOIN users u ON c.user_id=u.id WHERE c.status='approved'"
        params = []
        if city:
            sql += " AND (c.city LIKE %s OR c.city = 'All Cities in Tamilnadu')"
            params.append(f'%{city}%')
        if veg_type:
            sql += " AND c.veg_non_veg=%s"
            params.append(veg_type)
        sql += " ORDER BY c.price_per_plate"
        cursor.execute(sql, params)
        return jsonify(cursor.fetchall())
    finally:
        cursor.close(); conn.close()

@services_bp.route('/catering/<int:cat_id>', methods=['GET'])
def get_catering(cat_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM catering_companies WHERE id=%s", (cat_id,))
        company = cursor.fetchone()
        if not company:
            return jsonify({'error': 'Not found'}), 404
        cursor.execute("SELECT * FROM catering_menu WHERE catering_id=%s", (cat_id,))
        company['menu'] = cursor.fetchall()
        return jsonify(company)
    finally:
        cursor.close(); conn.close()

# ─── LUXURY CARS ──────────────────────────────────────────────────────────────
@services_bp.route('/cars', methods=['GET'])
def list_cars():
    city = request.args.get('city', '')
    decorated = request.args.get('decorated', '')
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        sql = "SELECT lc.*, u.name as vendor_name FROM luxury_cars lc LEFT JOIN users u ON lc.user_id=u.id WHERE lc.status='approved'"
        params = []
        if city:
            sql += " AND (lc.city LIKE %s OR lc.city = 'All Cities in Tamilnadu')"
            params.append(f'%{city}%')
        if decorated == 'true':
            sql += " AND lc.with_decorations=1"
        sql += " ORDER BY lc.rate_per_km"
        cursor.execute(sql, params)
        return jsonify(cursor.fetchall())
    finally:
        cursor.close(); conn.close()

# ─── PHOTOGRAPHY ──────────────────────────────────────────────────────────────
@services_bp.route('/photography', methods=['GET'])
def list_photography():
    city = request.args.get('city', '')
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        sql = "SELECT ps.*, u.name as vendor_name FROM photography_services ps LEFT JOIN users u ON ps.user_id=u.id WHERE ps.status='approved'"
        params = []
        if city:
            sql += " AND (ps.city LIKE %s OR ps.city = 'All Cities in Tamilnadu')"
            params.append(f'%{city}%')
        sql += " ORDER BY ps.base_price"
        cursor.execute(sql, params)
        return jsonify(cursor.fetchall())
    finally:
        cursor.close(); conn.close()

# ─── DECORATIONS ──────────────────────────────────────────────────────────────
@services_bp.route('/decorations', methods=['GET'])
def list_decorations():
    city = request.args.get('city', '')
    style = request.args.get('style', '')
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        sql = "SELECT d.*, u.name as vendor_name FROM decorations d LEFT JOIN users u ON d.user_id=u.id WHERE d.status='approved'"
        params = []
        if city:
            sql += " AND (d.city LIKE %s OR d.city = 'All Cities in Tamilnadu')"
            params.append(f'%{city}%')
        if style:
            sql += " AND (d.religion_style LIKE %s OR d.culture_style LIKE %s)"
            params += [f'%{style}%', f'%{style}%']
        sql += " ORDER BY d.base_price"
        cursor.execute(sql, params)
        return jsonify(cursor.fetchall())
    finally:
        cursor.close(); conn.close()

# ─── CITIES ───────────────────────────────────────────────────────────────────
@services_bp.route('/cities', methods=['GET'])
def list_cities():
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT DISTINCT city FROM halls WHERE city IS NOT NULL ORDER BY city")
        cities = [r[0] for r in cursor.fetchall()]
        return jsonify(cities)
    finally:
        cursor.close(); conn.close()

# ─── GENERIC ──────────────────────────────────────────────────────────────────
@services_bp.route('/services/detail', methods=['GET'])
def get_service_detail():
    stype = request.args.get('type')
    sid = request.args.get('id')
    if not all([stype, sid]):
        return jsonify({'error': 'type and id are required'}), 400
    
    table_map = {
        'hall': ('halls', 'vendor_id'),
        'catering': ('catering_companies', 'user_id'),
        'luxury_car': ('luxury_cars', 'user_id'),
        'photography': ('photography_services', 'user_id'),
        'decorations': ('decorations', 'user_id')
    }
    if stype not in table_map:
        return jsonify({'error': 'Invalid type'}), 400
        
    table, user_col = table_map[stype]
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        sql = f"SELECT s.*, u.name as vendor_name, u.phone as vendor_phone, u.email as vendor_email FROM {table} s LEFT JOIN users u ON s.{user_col}=u.id WHERE s.id=%s"
        cursor.execute(sql, (sid,))
        service = cursor.fetchone()
        if not service:
            return jsonify({'error': 'Not found'}), 404
        return jsonify(service)
    finally:
        cursor.close(); conn.close()
@services_bp.route('/services/availability', methods=['GET'])
def get_service_availability():
    stype = request.args.get('type')
    sid = request.args.get('id')
    if not all([stype, sid]):
        return jsonify({'error': 'type and id are required'}), 400
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # Get all confirmed bookings for this service
        cursor.execute("SELECT date FROM bookings WHERE service_type=%s AND service_id=%s AND status IN ('confirmed', 'paid')", (stype, sid))
        rows = cursor.fetchall()
        # Extract dates and convert to ISO strings
        booked_dates = []
        for r in rows:
            d = r['date']
            if hasattr(d, 'isoformat'):
                booked_dates.append(d.isoformat())
            else:
                booked_dates.append(str(d))
        return jsonify({'booked_dates': booked_dates})
    finally:
        cursor.close(); conn.close()
