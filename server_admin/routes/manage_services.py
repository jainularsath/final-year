"""Admin service management - full CRUD for all 5 service types."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from flask import Blueprint, request, jsonify, session
from db import get_db

services_bp = Blueprint('services_admin', __name__)

def require_admin():
    return session.get('role') == 'admin'

# ─── HALLS ────────────────────────────────────────────────────────────────────
@services_bp.route('/admin/halls', methods=['GET'])
def list_halls():
    if not require_admin(): return jsonify({'error': 'Forbidden'}), 403
    conn = get_db(); cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT h.*, u.name as vendor_name FROM halls h LEFT JOIN users u ON h.vendor_id=u.id ORDER BY h.id DESC")
        return jsonify(cursor.fetchall())
    finally: cursor.close(); conn.close()

@services_bp.route('/admin/halls', methods=['POST'])
def add_hall():
    if not require_admin(): return jsonify({'error': 'Forbidden'}), 403
    d = request.get_json()
    conn = get_db(); cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO halls (name,city,capacity,amenities,price_per_night,address,latitude,longitude,vendor_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (d.get('name'), d.get('city'), d.get('capacity'), d.get('amenities'),
             d.get('price_per_night'), d.get('address'), d.get('latitude'), d.get('longitude'), d.get('vendor_id'))
        )
        conn.commit()
        return jsonify({'id': cursor.lastrowid, 'message': 'Hall added'}), 201
    finally: cursor.close(); conn.close()

@services_bp.route('/admin/halls/<int:hall_id>', methods=['PUT'])
def update_hall(hall_id):
    if not require_admin(): return jsonify({'error': 'Forbidden'}), 403
    d = request.get_json()
    conn = get_db(); cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE halls SET name=%s,city=%s,capacity=%s,amenities=%s,price_per_night=%s,address=%s WHERE id=%s",
            (d.get('name'), d.get('city'), d.get('capacity'), d.get('amenities'), d.get('price_per_night'), d.get('address'), hall_id)
        )
        conn.commit()
        return jsonify({'message': 'Hall updated'})
    finally: cursor.close(); conn.close()

@services_bp.route('/admin/halls/<int:hall_id>', methods=['DELETE'])
def delete_hall(hall_id):
    if not require_admin(): return jsonify({'error': 'Forbidden'}), 403
    conn = get_db(); cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM halls WHERE id=%s", (hall_id,))
        conn.commit()
        return jsonify({'message': 'Hall deleted'})
    finally: cursor.close(); conn.close()

# ─── CATERING ─────────────────────────────────────────────────────────────────
@services_bp.route('/admin/catering', methods=['GET'])
def list_catering():
    if not require_admin(): return jsonify({'error': 'Forbidden'}), 403
    conn = get_db(); cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT c.*, u.name as vendor_name FROM catering_companies c LEFT JOIN users u ON c.user_id=u.id ORDER BY c.id DESC")
        return jsonify(cursor.fetchall())
    finally: cursor.close(); conn.close()

@services_bp.route('/admin/catering', methods=['POST'])
def add_catering():
    if not require_admin(): return jsonify({'error': 'Forbidden'}), 403
    d = request.get_json()
    conn = get_db(); cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO catering_companies (user_id,company_name,city,veg_non_veg,price_per_plate) VALUES (%s,%s,%s,%s,%s)",
            (d.get('user_id'), d.get('company_name'), d.get('city'), d.get('veg_non_veg','both'), d.get('price_per_plate'))
        )
        conn.commit()
        return jsonify({'id': cursor.lastrowid, 'message': 'Catering company added'}), 201
    finally: cursor.close(); conn.close()

@services_bp.route('/admin/catering/<int:cat_id>', methods=['PUT'])
def update_catering(cat_id):
    if not require_admin(): return jsonify({'error': 'Forbidden'}), 403
    d = request.get_json()
    conn = get_db(); cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE catering_companies SET company_name=%s,city=%s,veg_non_veg=%s,price_per_plate=%s WHERE id=%s",
            (d.get('company_name'), d.get('city'), d.get('veg_non_veg'), d.get('price_per_plate'), cat_id)
        )
        conn.commit()
        return jsonify({'message': 'Catering updated'})
    finally: cursor.close(); conn.close()

@services_bp.route('/admin/catering/<int:cat_id>', methods=['DELETE'])
def delete_catering(cat_id):
    if not require_admin(): return jsonify({'error': 'Forbidden'}), 403
    conn = get_db(); cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM catering_companies WHERE id=%s", (cat_id,))
        conn.commit()
        return jsonify({'message': 'Catering deleted'})
    finally: cursor.close(); conn.close()

# ─── LUXURY CARS ──────────────────────────────────────────────────────────────
@services_bp.route('/admin/cars', methods=['GET'])
def list_cars():
    if not require_admin(): return jsonify({'error': 'Forbidden'}), 403
    conn = get_db(); cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT lc.*, u.name as vendor_name FROM luxury_cars lc LEFT JOIN users u ON lc.user_id=u.id ORDER BY lc.id DESC")
        return jsonify(cursor.fetchall())
    finally: cursor.close(); conn.close()

@services_bp.route('/admin/cars', methods=['POST'])
def add_car():
    if not require_admin(): return jsonify({'error': 'Forbidden'}), 403
    d = request.get_json()
    conn = get_db(); cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO luxury_cars (user_id,car_name,car_model,city,image_url,rate_per_km,capacity,with_decorations) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (d.get('user_id'), d.get('car_name'), d.get('car_model'), d.get('city'),
             d.get('image_url',''), d.get('rate_per_km'), d.get('capacity'), d.get('with_decorations', False))
        )
        conn.commit()
        return jsonify({'id': cursor.lastrowid, 'message': 'Car added'}), 201
    finally: cursor.close(); conn.close()

@services_bp.route('/admin/cars/<int:car_id>', methods=['PUT'])
def update_car(car_id):
    if not require_admin(): return jsonify({'error': 'Forbidden'}), 403
    d = request.get_json()
    conn = get_db(); cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE luxury_cars SET car_name=%s,car_model=%s,city=%s,rate_per_km=%s,capacity=%s,with_decorations=%s WHERE id=%s",
            (d.get('car_name'), d.get('car_model'), d.get('city'), d.get('rate_per_km'), d.get('capacity'), d.get('with_decorations', False), car_id)
        )
        conn.commit()
        return jsonify({'message': 'Car updated'})
    finally: cursor.close(); conn.close()

@services_bp.route('/admin/cars/<int:car_id>', methods=['DELETE'])
def delete_car(car_id):
    if not require_admin(): return jsonify({'error': 'Forbidden'}), 403
    conn = get_db(); cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM luxury_cars WHERE id=%s", (car_id,))
        conn.commit()
        return jsonify({'message': 'Car deleted'})
    finally: cursor.close(); conn.close()

# ─── PHOTOGRAPHY ──────────────────────────────────────────────────────────────
@services_bp.route('/admin/photography', methods=['GET'])
def list_photography():
    if not require_admin(): return jsonify({'error': 'Forbidden'}), 403
    conn = get_db(); cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT ps.*, u.name as vendor_name FROM photography_services ps LEFT JOIN users u ON ps.user_id=u.id ORDER BY ps.id DESC")
        return jsonify(cursor.fetchall())
    finally: cursor.close(); conn.close()

@services_bp.route('/admin/photography', methods=['POST'])
def add_photography():
    if not require_admin(): return jsonify({'error': 'Forbidden'}), 403
    d = request.get_json()
    conn = get_db(); cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO photography_services (city,service_name,base_price,price_per_hour,user_id) VALUES (%s,%s,%s,%s,%s)",
            (d.get('city'), d.get('service_name'), d.get('base_price'), d.get('price_per_hour'), d.get('user_id'))
        )
        conn.commit()
        return jsonify({'id': cursor.lastrowid, 'message': 'Photography service added'}), 201
    finally: cursor.close(); conn.close()

@services_bp.route('/admin/photography/<int:photo_id>', methods=['PUT'])
def update_photography(photo_id):
    if not require_admin(): return jsonify({'error': 'Forbidden'}), 403
    d = request.get_json()
    conn = get_db(); cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE photography_services SET city=%s,service_name=%s,base_price=%s,price_per_hour=%s WHERE id=%s",
            (d.get('city'), d.get('service_name'), d.get('base_price'), d.get('price_per_hour'), photo_id)
        )
        conn.commit()
        return jsonify({'message': 'Photography updated'})
    finally: cursor.close(); conn.close()

@services_bp.route('/admin/photography/<int:photo_id>', methods=['DELETE'])
def delete_photography(photo_id):
    if not require_admin(): return jsonify({'error': 'Forbidden'}), 403
    conn = get_db(); cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM photography_services WHERE id=%s", (photo_id,))
        conn.commit()
        return jsonify({'message': 'Photography service deleted'})
    finally: cursor.close(); conn.close()

# ─── DECORATIONS ──────────────────────────────────────────────────────────────
@services_bp.route('/admin/decorations', methods=['GET'])
def list_decorations():
    if not require_admin(): return jsonify({'error': 'Forbidden'}), 403
    conn = get_db(); cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT d.*, u.name as vendor_name FROM decorations d LEFT JOIN users u ON d.user_id=u.id ORDER BY d.id DESC")
        return jsonify(cursor.fetchall())
    finally: cursor.close(); conn.close()

@services_bp.route('/admin/decorations', methods=['POST'])
def add_decoration():
    if not require_admin(): return jsonify({'error': 'Forbidden'}), 403
    d = request.get_json()
    conn = get_db(); cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO decorations (user_id,theme_name,religion_style,culture_style,base_price,city) VALUES (%s,%s,%s,%s,%s,%s)",
            (d.get('user_id'), d.get('theme_name'), d.get('religion_style'), d.get('culture_style'), d.get('base_price'), d.get('city'))
        )
        conn.commit()
        return jsonify({'id': cursor.lastrowid, 'message': 'Decoration added'}), 201
    finally: cursor.close(); conn.close()

@services_bp.route('/admin/decorations/<int:decor_id>', methods=['PUT'])
def update_decoration(decor_id):
    if not require_admin(): return jsonify({'error': 'Forbidden'}), 403
    d = request.get_json()
    conn = get_db(); cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE decorations SET theme_name=%s,religion_style=%s,culture_style=%s,base_price=%s,city=%s WHERE id=%s",
            (d.get('theme_name'), d.get('religion_style'), d.get('culture_style'), d.get('base_price'), d.get('city'), decor_id)
        )
        conn.commit()
        return jsonify({'message': 'Decoration updated'})
    finally: cursor.close(); conn.close()

@services_bp.route('/admin/decorations/<int:decor_id>', methods=['DELETE'])
def delete_decoration(decor_id):
    if not require_admin(): return jsonify({'error': 'Forbidden'}), 403
    conn = get_db(); cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM decorations WHERE id=%s", (decor_id,))
        conn.commit()
        return jsonify({'message': 'Decoration deleted'})
    finally: cursor.close(); conn.close()

# ─── SERVICE STATUS UPDATE ────────────────────────────────────────────────────
@services_bp.route('/admin/<string:stype>/<int:sid>/status', methods=['PUT'])
def update_service_status(stype, sid):
    if not require_admin(): return jsonify({'error': 'Forbidden'}), 403
    status = request.get_json().get('status')
    if status not in ('pending', 'approved', 'rejected'):
        return jsonify({'error': 'Invalid status'}), 400
        
    table_map = {
        'halls': 'halls',
        'catering': 'catering_companies',
        'cars': 'luxury_cars',
        'photography': 'photography_services',
        'decorations': 'decorations'
    }
    
    if stype not in table_map:
        return jsonify({'error': 'Invalid service type'}), 400
        
    table = table_map[stype]
    conn = get_db(); cursor = conn.cursor()
    try:
        cursor.execute(f"UPDATE {table} SET status=%s WHERE id=%s", (status, sid))
        conn.commit()
        return jsonify({'message': 'Status updated successfully'})
    finally: cursor.close(); conn.close()
