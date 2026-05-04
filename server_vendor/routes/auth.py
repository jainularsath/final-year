"""Auth routes for vendor server (port 3001)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import bcrypt
from flask import Blueprint, request, jsonify, session, redirect
from db import get_db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name','').strip()
    email = data.get('email','').strip().lower()
    phone = data.get('phone','').strip()
    vendor_service_type = data.get('service_type','').strip()
    password = data.get('password','')
    
    if not all([name, email, password, vendor_service_type]):
        return jsonify({'error': 'Name, email, password and service type are required'}), 400

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            return jsonify({'error': 'Email already registered'}), 409
        cursor.execute(
            "INSERT INTO users (name,email,phone,password_hash,role,vendor_service_type,status) VALUES (%s,%s,%s,%s,'vendor',%s,'pending')",
            (name, email, phone, hashed, vendor_service_type)
        )
        vendor_id = cursor.lastrowid
        # Create a pending approval record
        cursor.execute(
            "INSERT INTO vendor_approvals (vendor_id, status) VALUES (%s,'pending')",
            (vendor_id,)
        )
        conn.commit()
        return jsonify({'message': 'Registration submitted. Awaiting admin approval.'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close(); conn.close()

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email','').strip().lower()
    password = data.get('password','')

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE email=%s AND role='vendor'", (email,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        if user['status'] == 'pending':
            return jsonify({'error': 'Your account is pending admin approval'}), 403
        if user['status'] != 'active':
            return jsonify({'error': 'Account is inactive'}), 403
        if not bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
            return jsonify({'error': 'Invalid credentials'}), 401
        session['user_id'] = user['id']
        session['role'] = 'vendor'
        session['name'] = user['name']
        session.permanent = True
        return jsonify({'message': 'Login successful', 'user': {'id': user['id'], 'name': user['name'], 'role': 'vendor'}}), 200
    finally:
        cursor.close(); conn.close()

@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    return redirect('http://localhost:3001/login.html')

@auth_bp.route('/me', methods=['GET'])
def me():
    if 'user_id' not in session or session.get('role') != 'vendor':
        return jsonify({'error': 'Not authenticated'}), 401
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id,name,email,phone,role,status FROM users WHERE id=%s", (session['user_id'],))
        user = cursor.fetchone()
        return jsonify(user) if user else (jsonify({'error': 'User not found'}), 404)
    finally:
        cursor.close(); conn.close()
@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    if 'user_id' not in session or session.get('role') != 'vendor':
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
