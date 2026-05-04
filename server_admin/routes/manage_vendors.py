"""Admin vendor management - approve/reject vendors."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from flask import Blueprint, request, jsonify, session
from db import get_db
from datetime import datetime

vendors_bp = Blueprint('vendors', __name__)

def require_admin():
    if session.get('role') != 'admin':
        return None
    return session.get('user_id')

@vendors_bp.route('/admin/vendors', methods=['GET'])
def list_vendors():
    if not require_admin():
        return jsonify({'error': 'Forbidden'}), 403
    status = request.args.get('status', '')
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        sql = "SELECT u.id, u.name, u.email, u.phone, u.status, u.created_at, va.status as approval_status FROM users u LEFT JOIN vendor_approvals va ON va.vendor_id=u.id WHERE u.role='vendor'"
        params = []
        if status:
            sql += " AND u.status=%s"
            params.append(status)
        sql += " ORDER BY u.created_at DESC"
        cursor.execute(sql, params)
        vendors = cursor.fetchall()
        for v in vendors:
            if hasattr(v.get('created_at'), 'isoformat'):
                v['created_at'] = v['created_at'].isoformat()
        return jsonify(vendors)
    finally:
        cursor.close(); conn.close()

@vendors_bp.route('/admin/vendors/<int:vendor_id>/approve', methods=['POST'])
def approve_vendor(vendor_id):
    admin_id = require_admin()
    if not admin_id:
        return jsonify({'error': 'Forbidden'}), 403
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET status='active' WHERE id=%s AND role='vendor'", (vendor_id,))
        cursor.execute("""
            INSERT INTO vendor_approvals (vendor_id, approved_by_admin_id, approved_at, status)
            VALUES (%s, %s, %s, 'approved')
            ON DUPLICATE KEY UPDATE status='approved', approved_by_admin_id=%s, approved_at=%s
        """, (vendor_id, admin_id, datetime.now(), admin_id, datetime.now()))
        conn.commit()
        return jsonify({'message': 'Vendor approved'})
    finally:
        cursor.close(); conn.close()

@vendors_bp.route('/admin/vendors/<int:vendor_id>/reject', methods=['POST'])
def reject_vendor(vendor_id):
    admin_id = require_admin()
    if not admin_id:
        return jsonify({'error': 'Forbidden'}), 403
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET status='inactive' WHERE id=%s AND role='vendor'", (vendor_id,))
        cursor.execute("""
            INSERT INTO vendor_approvals (vendor_id, approved_by_admin_id, approved_at, status)
            VALUES (%s, %s, %s, 'rejected')
            ON DUPLICATE KEY UPDATE status='rejected', approved_by_admin_id=%s, approved_at=%s
        """, (vendor_id, admin_id, datetime.now(), admin_id, datetime.now()))
        conn.commit()
        return jsonify({'message': 'Vendor rejected'})
    finally:
        cursor.close(); conn.close()

@vendors_bp.route('/admin/vendors/<int:vendor_id>', methods=['DELETE'])
def delete_vendor(vendor_id):
    if not require_admin():
        return jsonify({'error': 'Forbidden'}), 403
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE id=%s AND role='vendor'", (vendor_id,))
        conn.commit()
        return jsonify({'message': 'Vendor deleted'})
    finally:
        cursor.close(); conn.close()

@vendors_bp.route('/admin/users', methods=['GET'])
def list_users():
    if not require_admin():
        return jsonify({'error': 'Forbidden'}), 403
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id,name,email,phone,status,created_at FROM users WHERE role='user' ORDER BY created_at DESC")
        users = cursor.fetchall()
        for u in users:
            if hasattr(u.get('created_at'), 'isoformat'):
                u['created_at'] = u['created_at'].isoformat()
        return jsonify(users)
    finally:
        cursor.close(); conn.close()

@vendors_bp.route('/admin/bookings', methods=['GET'])
def list_all_bookings():
    if not require_admin():
        return jsonify({'error': 'Forbidden'}), 403
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT b.*, u.name as customer_name,
                CASE b.service_type
                    WHEN 'hall' THEN (SELECT name FROM halls WHERE id=b.service_id)
                    WHEN 'catering' THEN (SELECT company_name FROM catering_companies WHERE id=b.service_id)
                    WHEN 'luxury_car' THEN (SELECT CONCAT(car_name,' ',car_model) FROM luxury_cars WHERE id=b.service_id)
                    WHEN 'photography' THEN (SELECT service_name FROM photography_services WHERE id=b.service_id)
                    WHEN 'decorations' THEN (SELECT theme_name FROM decorations WHERE id=b.service_id)
                END as service_name
            FROM bookings b JOIN users u ON b.user_id=u.id
            ORDER BY b.created_at DESC LIMIT 200
        """)
        bookings = cursor.fetchall()
        for b in bookings:
            for k, v in b.items():
                if hasattr(v, 'isoformat'):
                    b[k] = v.isoformat()
        return jsonify(bookings)
    finally:
        cursor.close(); conn.close()
