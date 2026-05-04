"""Admin auth routes - admin-only login/logout."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import bcrypt
from flask import Blueprint, request, jsonify, session, redirect
from db import get_db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE email=%s AND role='admin'", (email,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        if not bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
            return jsonify({'error': 'Invalid credentials'}), 401
        session['user_id'] = user['id']
        session['role'] = 'admin'
        session['name'] = user['name']
        session.permanent = True
        return jsonify({'message': 'Login successful', 'user': {'id': user['id'], 'name': user['name'], 'role': 'admin'}}), 200
    finally:
        cursor.close(); conn.close()

@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    return redirect('http://localhost:3002/login.html')

@auth_bp.route('/me', methods=['GET'])
def me():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Not authenticated'}), 401
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id,name,email,role FROM users WHERE id=%s", (session['user_id'],))
        user = cursor.fetchone()
        return jsonify(user) if user else (jsonify({'error': 'Not found'}), 404)
    finally:
        cursor.close(); conn.close()

# ─── DASHBOARD STATS ──────────────────────────────────────────────────────────
@auth_bp.route('/admin/stats', methods=['GET'])
def stats():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) as total FROM users WHERE role='user'")
        total_users = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) as total FROM users WHERE role='vendor' AND status='active'")
        total_vendors = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) as total FROM users WHERE role='vendor' AND status='pending'")
        pending_vendors = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) as total FROM bookings")
        total_bookings = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) as total FROM bookings WHERE status='pending'")
        pending_bookings = cursor.fetchone()['total']
        cursor.execute("SELECT COALESCE(SUM(total_amount),0) as revenue FROM bookings WHERE status IN ('confirmed','completed')")
        revenue = cursor.fetchone()['revenue']
        cursor.execute("SELECT COUNT(*) as total FROM halls")
        total_halls = cursor.fetchone()['total']
        return jsonify({
            'total_users': total_users,
            'total_vendors': total_vendors,
            'pending_vendors': pending_vendors,
            'total_bookings': total_bookings,
            'pending_bookings': pending_bookings,
            'total_revenue': float(revenue),
            'total_halls': total_halls
        })
    finally:
        cursor.close(); conn.close()
@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    old_pw = data.get('old_password')
    new_pw = data.get('new_password')
    
    if not old_pw or not new_pw:
        return jsonify({'error': 'Old and new passwords are required'}), 400
        
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT password_hash FROM users WHERE id=%s", (session['user_id'],))
        user = cursor.fetchone()
        if not user or not bcrypt.checkpw(old_pw.encode(), user['password_hash'].encode()):
            return jsonify({'error': 'Incorrect current password'}), 400
            
        hashed = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
        cursor.execute("UPDATE users SET password_hash=%s WHERE id=%s", (hashed, session['user_id']))
        conn.commit()
        return jsonify({'message': 'Password updated successfully'})
    finally:
        cursor.close(); conn.close()
