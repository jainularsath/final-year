"""Booking routes for user server."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from flask import Blueprint, request, jsonify, session
from db import get_db

booking_bp = Blueprint('booking', __name__)

def require_user():
    if 'user_id' not in session or session.get('role') != 'user':
        return None
    return session['user_id']

@booking_bp.route('/bookings', methods=['POST'])
def create_booking():
    user_id = require_user()
    if not user_id:
        return jsonify({'error': 'Login required', 'login_required': True}), 401

    data = request.get_json()
    service_type = data.get('service_type')
    service_id = data.get('service_id')
    date = data.get('date')
    time = data.get('time', '10:00:00')
    total_people = data.get('total_people', 1)
    total_amount = data.get('total_amount', 0)
    advance_amount = data.get('advance_amount', 0)
    notes = data.get('notes', '')

    if not all([service_type, service_id, date]):
        return jsonify({'error': 'service_type, service_id, date are required'}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM bookings WHERE service_type=%s AND service_id=%s AND date=%s AND status IN ('confirmed', 'paid')", (service_type, service_id, date))
        if cursor.fetchone():
            return jsonify({'error': 'This date is already booked and unavailable for this service.'}), 400

        cursor.execute(
            """INSERT INTO bookings 
               (user_id,service_type,service_id,date,time,total_people,total_amount,advance_amount,notes,status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'pending')""",
            (user_id, service_type, service_id, date, time, total_people, total_amount, advance_amount, notes)
        )
        conn.commit()
        booking_id = cursor.lastrowid
        return jsonify({'message': 'Booking created', 'booking_id': booking_id, 'status': 'pending'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close(); conn.close()

@booking_bp.route('/bookings', methods=['GET'])
def get_my_bookings():
    user_id = require_user()
    if not user_id:
        return jsonify({'error': 'Login required', 'login_required': True}), 401

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT b.*, 
                CASE b.service_type
                    WHEN 'hall' THEN (SELECT name FROM halls WHERE id=b.service_id)
                    WHEN 'catering' THEN (SELECT company_name FROM catering_companies WHERE id=b.service_id)
                    WHEN 'luxury_car' THEN (SELECT CONCAT(car_name,' ',car_model) FROM luxury_cars WHERE id=b.service_id)
                    WHEN 'photography' THEN (SELECT service_name FROM photography_services WHERE id=b.service_id)
                    WHEN 'decorations' THEN (SELECT theme_name FROM decorations WHERE id=b.service_id)
                END as service_name
            FROM bookings b WHERE b.user_id=%s ORDER BY b.created_at DESC
        """, (user_id,))
        bookings = cursor.fetchall()
        for b in bookings:
            for k, v in b.items():
                if hasattr(v, 'isoformat'):
                    b[k] = v.isoformat()
        return jsonify(bookings)
    finally:
        cursor.close(); conn.close()

@booking_bp.route('/bookings/<int:booking_id>', methods=['GET'])
def get_booking(booking_id):
    user_id = require_user()
    if not user_id:
        return jsonify({'error': 'Login required', 'login_required': True}), 401
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM bookings WHERE id=%s AND user_id=%s", (booking_id, user_id))
        booking = cursor.fetchone()
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        for k, v in booking.items():
            if hasattr(v, 'isoformat'):
                booking[k] = v.isoformat()
        return jsonify(booking)
    finally:
        cursor.close(); conn.close()

@booking_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
def cancel_booking(booking_id):
    user_id = require_user()
    if not user_id:
        return jsonify({'error': 'Login required', 'login_required': True}), 401
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Check current status first to decide which cancellation status to use
        cursor.execute("SELECT status FROM bookings WHERE id=%s AND user_id=%s", (booking_id, user_id))
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Booking not found'}), 404
        
        current_status = row[0]
        new_status = 'cancelled'
        if current_status == 'confirmed':
            new_status = 'cancelled_no_refund'
        elif current_status != 'pending':
            return jsonify({'error': f'Cannot cancel a booking in {current_status} status'}), 400

        cursor.execute(
            "UPDATE bookings SET status=%s WHERE id=%s AND user_id=%s",
            (new_status, booking_id, user_id)
        )
        conn.commit()
        return jsonify({'message': 'Booking cancelled', 'new_status': new_status})
    finally:
        cursor.close(); conn.close()

from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from flask import send_file

@booking_bp.route('/bookings/<int:booking_id>/pay', methods=['POST'])
def pay_booking(booking_id):
    user_id = require_user()
    if not user_id:
        return jsonify({'error': 'Login required'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE bookings SET status='pending' WHERE id=%s AND user_id=%s", (booking_id, user_id))
        conn.commit()
        return jsonify({'message': 'Payment confirmed. Waiting for vendor acceptance.', 'status': 'pending'})
    finally:
        cursor.close(); conn.close()

@booking_bp.route('/bookings/<int:booking_id>/invoice', methods=['GET'])
def download_invoice(booking_id):
    user_id = require_user()
    if not user_id:
        return jsonify({'error': 'Login required'}), 401

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT b.*, u.name as customer_name, u.email as customer_email,
                CASE b.service_type
                    WHEN 'hall' THEN (SELECT name FROM halls WHERE id=b.service_id)
                    WHEN 'catering' THEN (SELECT company_name FROM catering_companies WHERE id=b.service_id)
                    WHEN 'luxury_car' THEN (SELECT CONCAT(car_name,' ',car_model) FROM luxury_cars WHERE id=b.service_id)
                    WHEN 'photography' THEN (SELECT service_name FROM photography_services WHERE id=b.service_id)
                    WHEN 'decorations' THEN (SELECT theme_name FROM decorations WHERE id=b.service_id)
                END as service_name
            FROM bookings b JOIN users u ON b.user_id=u.id 
            WHERE b.id=%s AND (b.user_id=%s OR u.role='admin')
        """, (booking_id, user_id))
        b = cursor.fetchone()
        if not b:
            return "Booking not found", 404

        # Generate PDF
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Header
        p.setFont("Helvetica-Bold", 24)
        p.drawCentredString(width/2, height - 50, "TN EVENTS - INVOICE")
        
        p.setFont("Helvetica", 12)
        p.drawString(50, height - 100, f"Invoice ID: INV-{b['id']}")
        p.drawString(50, height - 120, f"Date: {b['created_at']}")
        
        # Customer Info
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, height - 160, "Bill To:")
        p.setFont("Helvetica", 12)
        p.drawString(50, height - 180, f"Name: {b['customer_name']}")
        p.drawString(50, height - 200, f"Email: {b['customer_email']}")
        
        # Details
        p.setStrokeColor(colors.grey)
        p.line(50, height - 220, width - 50, height - 220)
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, height - 240, "Service Description")
        p.drawString(400, height - 240, "Amount (₹)")
        
        p.setFont("Helvetica", 12)
        p.drawString(50, height - 265, f"{b['service_type'].upper()}: {b['service_name']}")
        p.drawString(400, height - 265, f"₹{b['total_amount']:,}")
        
        p.line(50, height - 280, width - 50, height - 280)
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(300, height - 300, "Advance Paid:")
        p.drawString(400, height - 300, f"₹{b['advance_amount']:,}")
        
        p.setFont("Helvetica-Bold", 14)
        p.setFillColor(colors.darkgreen)
        p.drawString(300, height - 330, "Status:")
        p.drawString(400, height - 330, f"{b['status'].upper()}")
        
        # Footer
        p.setFont("Helvetica-Oblique", 10)
        p.setFillColor(colors.black)
        p.drawCentredString(width/2, 50, "Thank you for choosing TN Events!")
        
        p.showPage()
        p.save()
        
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=f"invoice_{booking_id}.pdf", mimetype='application/pdf')
    finally:
        cursor.close(); conn.close()

@booking_bp.route('/payment', methods=['POST'])
def process_payment():
    """Simulated payment processing."""
    user_id = require_user()
    if not user_id:
        return jsonify({'error': 'Login required', 'login_required': True}), 401
    data = request.get_json()
    booking_id = data.get('booking_id')
    amount = data.get('amount')
    
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE bookings SET status='pending' WHERE id=%s AND user_id=%s", (booking_id, user_id))
        conn.commit()
        return jsonify({
            'message': 'Payment successful. Waiting for vendor acceptance.',
            'transaction_id': f'TXN{booking_id}{amount}',
            'booking_id': booking_id,
            'amount_paid': amount,
            'status': 'pending'
        })
    finally:
        cursor.close(); conn.close()

