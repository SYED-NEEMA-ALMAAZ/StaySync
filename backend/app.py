# =============================================================
#  StaySync — Complete Flask Backend
#  Covers: Auth, Rooms, Bookings, Complaints, Leaves,
#          Fees/Payments, Fines, Visitors, Notifications,
#          Maintenance, Attendance, Students, Users (Admin)
# =============================================================

# ── Imports ───────────────────────────────────────────────────
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from dotenv import load_dotenv
from datetime import datetime
import bcrypt
import os

# ── Load .env ─────────────────────────────────────────────────
load_dotenv()

# ── App setup ─────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@localhost/{os.getenv('DB_NAME')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'staysync-secret-key')

db  = SQLAlchemy(app)
jwt = JWTManager(app)


# =============================================================
#  MODELS
# =============================================================

class User(db.Model):
    __tablename__ = 'users'
    user_id    = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(100), unique=True, nullable=False)
    password   = db.Column(db.String(255), nullable=False)
    role       = db.Column(db.String(50),  nullable=False)   # student | warden | admin | maintenance
    staff_id   = db.Column(db.String(50),  nullable=True)    # student/staff ID shown on frontend
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Student(db.Model):
    __tablename__ = 'students'
    student_id = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    room_id    = db.Column(db.Integer, db.ForeignKey('rooms.room_id'), nullable=True)
    course     = db.Column(db.String(100))
    year       = db.Column(db.Integer)


class Room(db.Model):
    __tablename__ = 'rooms'
    room_id     = db.Column(db.Integer, primary_key=True)
    room_no     = db.Column(db.String(20))           # e.g. "A-101"
    block       = db.Column(db.String(50))
    type        = db.Column(db.String(50))           # Single / Double / Triple / Dormitory
    floor       = db.Column(db.Integer, default=1)
    capacity    = db.Column(db.Integer)
    occupied    = db.Column(db.Integer, default=0)
    price       = db.Column(db.Float)
    status      = db.Column(db.String(50), default='Available')  # Available | Occupied | Maintenance
    amenities   = db.Column(db.Text)                # JSON string e.g. '["WiFi","AC"]'
    description = db.Column(db.Text)
    image_url   = db.Column(db.String(500))


class Booking(db.Model):
    __tablename__ = 'bookings'
    booking_id       = db.Column(db.Integer, primary_key=True)
    student_id       = db.Column(db.Integer, db.ForeignKey('students.student_id'))
    room_id          = db.Column(db.Integer, db.ForeignKey('rooms.room_id'))
    requested_on     = db.Column(db.DateTime, default=datetime.utcnow)
    approved_on      = db.Column(db.DateTime, nullable=True)
    approved_by      = db.Column(db.Integer,  db.ForeignKey('users.user_id'), nullable=True)
    status           = db.Column(db.String(20), default='Pending')  # Pending | Approved | Rejected | Cancelled
    rejection_reason = db.Column(db.String(255), nullable=True)
    notes            = db.Column(db.Text, nullable=True)
    # Frontend booking form fields
    full_name        = db.Column(db.String(100))
    room_type        = db.Column(db.String(50))
    preferred_block  = db.Column(db.String(50))
    checkin_date     = db.Column(db.String(20))
    duration         = db.Column(db.String(30))


class Complaint(db.Model):
    __tablename__ = 'complaints'
    complaint_id = db.Column(db.Integer, primary_key=True)
    student_id   = db.Column(db.Integer, db.ForeignKey('students.student_id'))
    category     = db.Column(db.String(50))   # Electrical | Plumbing | Furniture | Wi-Fi | Housekeeping | Other
    subject      = db.Column(db.String(150))
    description  = db.Column(db.Text)
    priority     = db.Column(db.String(20))   # Low | Medium | High | Critical
    status       = db.Column(db.String(50), default='Pending')   # Pending | In Progress | Resolved
    assigned_to  = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Leave(db.Model):
    __tablename__ = 'leaves'
    leave_id   = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'))
    type       = db.Column(db.String(50))    # Home Visit | Medical | Event | Other
    from_date  = db.Column(db.String(20))
    to_date    = db.Column(db.String(20))
    reason     = db.Column(db.Text)
    status     = db.Column(db.String(30), default='Pending')   # Pending | Approved | Rejected
    approved_by= db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Payment(db.Model):
    __tablename__ = 'payments'
    payment_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'))
    month      = db.Column(db.String(30))      # e.g. "April 2025"
    amount     = db.Column(db.Float)
    due_date   = db.Column(db.String(20))
    paid_date  = db.Column(db.String(20), nullable=True)
    method     = db.Column(db.String(30), nullable=True)   # UPI | Card | Net Banking | Cash
    status     = db.Column(db.String(20), default='Pending')   # Paid | Pending | Overdue
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Fine(db.Model):
    __tablename__ = 'fines'
    fine_id    = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'))
    title      = db.Column(db.String(150))
    amount     = db.Column(db.Float)
    reason     = db.Column(db.Text)
    status     = db.Column(db.String(20), default='Unpaid')   # Unpaid | Paid
    issued_on  = db.Column(db.DateTime, default=datetime.utcnow)
    paid_on    = db.Column(db.DateTime, nullable=True)


class Maintenance(db.Model):
    __tablename__ = 'maintenance'
    maintenance_id = db.Column(db.Integer, primary_key=True)
    room_id        = db.Column(db.Integer, db.ForeignKey('rooms.room_id'))
    reported_by    = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    issue          = db.Column(db.String(150))
    description    = db.Column(db.Text)
    status         = db.Column(db.String(30), default='Pending')   # Pending | In Progress | Done
    assigned_to    = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)


class Attendance(db.Model):
    __tablename__ = 'attendance'
    attendance_id = db.Column(db.Integer, primary_key=True)
    student_id    = db.Column(db.Integer, db.ForeignKey('students.student_id'))
    date          = db.Column(db.String(20))
    status        = db.Column(db.String(20), default='Present')   # Present | Absent | On-Leave


class Notification(db.Model):
    __tablename__ = 'notifications'
    notification_id = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)  # NULL = broadcast
    title           = db.Column(db.String(150))
    message         = db.Column(db.Text)
    type            = db.Column(db.String(30), default='info')   # info | success | warning | error | announcement
    is_read         = db.Column(db.Boolean, default=False)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)


class Visitor(db.Model):
    __tablename__ = 'visitors'
    visitor_id      = db.Column(db.Integer, primary_key=True)
    student_id      = db.Column(db.Integer, db.ForeignKey('students.student_id'))
    visitor_name    = db.Column(db.String(100))
    relation        = db.Column(db.String(50))
    phone           = db.Column(db.String(15))
    id_proof_type   = db.Column(db.String(50))
    id_proof_number = db.Column(db.String(50))
    purpose         = db.Column(db.String(255))
    checked_in_at   = db.Column(db.DateTime, default=datetime.utcnow)
    checked_out_at  = db.Column(db.DateTime, nullable=True)
    approved_by     = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    status          = db.Column(db.String(20), default='Checked In')   # Checked In | Checked Out | Denied


# =============================================================
#  HELPERS
# =============================================================

def current_user_id():
    """Return integer user_id from JWT token."""
    return int(get_jwt_identity())


def ok(data=None, msg="Success", code=200):
    payload = {"message": msg}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), code


def err(msg="Error", code=400):
    return jsonify({"error": msg}), code


# =============================================================
#  ① HOME
# =============================================================

@app.route('/')
def home():
    return jsonify({"status": "StaySync backend is running ✅"})


# =============================================================
#  ② AUTH — Register & Login
# =============================================================

@app.route('/register', methods=['POST'])
def register():
    """
    Body: { name, email, password, role, id? }
    role: student | warden | admin | maintenance
    """
    try:
        data = request.json
        if not data.get('email') or not data.get('password') or not data.get('name'):
            return err("name, email, and password are required")

        if User.query.filter_by(email=data['email']).first():
            return err("Email already registered", 400)

        hashed = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode()

        user = User(
            name     = data['name'],
            email    = data['email'],
            password = hashed,
            role     = data.get('role', 'student'),
            staff_id = data.get('id')
        )
        db.session.add(user)
        db.session.flush()   # get user_id before commit

        # Auto-create Student record for student role
        if user.role == 'student':
            student = Student(user_id=user.user_id)
            db.session.add(student)

        db.session.commit()

        token = create_access_token(identity=str(user.user_id))
        return ok({
            "token":   token,
            "user_id": user.user_id,
            "role":    user.role,
            "name":    user.name,
            "email":   user.email
        }, "Registered successfully", 201)

    except Exception as e:
        db.session.rollback()
        return err(str(e), 500)


@app.route('/login', methods=['POST'])
def login():
    """
    Body: { email, password }
    Returns: { token, role, name, email, user_id }
    """
    try:
        data = request.json
        user = User.query.filter_by(email=data.get('email', '')).first()

        if not user or not bcrypt.checkpw(
            data.get('password', '').encode(),
            user.password.encode()
        ):
            return err("Invalid email or password", 401)

        token = create_access_token(identity=str(user.user_id))

        # Get student_id if applicable
        student = Student.query.filter_by(user_id=user.user_id).first()

        return ok({
            "token":      token,
            "user_id":    user.user_id,
            "role":       user.role,
            "name":       user.name,
            "email":      user.email,
            "staff_id":   user.staff_id,
            "student_id": student.student_id if student else None
        }, "Login successful")

    except Exception as e:
        return err(str(e), 500)


# =============================================================
#  ③ PROFILE
# =============================================================

@app.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        uid  = current_user_id()
        user = User.query.get(uid)
        if not user:
            return err("User not found", 404)

        student = Student.query.filter_by(user_id=uid).first()
        return ok({
            "user_id":    user.user_id,
            "name":       user.name,
            "email":      user.email,
            "role":       user.role,
            "staff_id":   user.staff_id,
            "student_id": student.student_id if student else None,
            "room_id":    student.room_id    if student else None,
            "course":     student.course     if student else None,
            "year":       student.year       if student else None,
        })
    except Exception as e:
        return err(str(e), 500)


@app.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Body: { name?, course?, year? }"""
    try:
        uid  = current_user_id()
        data = request.json
        user = User.query.get(uid)
        if not user:
            return err("User not found", 404)

        if 'name' in data:
            user.name = data['name']

        student = Student.query.filter_by(user_id=uid).first()
        if student:
            if 'course' in data: student.course = data['course']
            if 'year'   in data: student.year   = data['year']

        db.session.commit()
        return ok(msg="Profile updated")

    except Exception as e:
        db.session.rollback()
        return err(str(e), 500)


# =============================================================
#  ④ ROOMS
# =============================================================

@app.route('/rooms', methods=['GET'])
@jwt_required()
def get_rooms():
    """
    Query params: block, status
    Returns list of rooms mapped to the format the frontend DB.rooms uses.
    """
    try:
        query = Room.query
        if request.args.get('block'):
            query = query.filter_by(block=request.args['block'])
        if request.args.get('status'):
            query = query.filter_by(status=request.args['status'])

        rooms = query.all()
        return ok([{
            "room_id":     r.room_id,
            "no":          r.room_no,          # maps to DB.rooms[i].no
            "block":       r.block,
            "type":        r.type,
            "floor":       r.floor,
            "cap":         r.capacity,         # maps to DB.rooms[i].cap
            "occ":         r.occupied,         # maps to DB.rooms[i].occ
            "fee":         r.price,            # maps to DB.rooms[i].fee
            "status":      r.status,
            "amenities":   r.amenities,
            "description": r.description,
            "img":         r.image_url,
        } for r in rooms])

    except Exception as e:
        return err(str(e), 500)


@app.route('/rooms', methods=['POST'])
@jwt_required()
def add_room():
    """Admin only. Body: { room_no, block, type, floor, capacity, price, amenities?, description? }"""
    try:
        data = request.json
        room = Room(
            room_no     = data['room_no'],
            block       = data['block'],
            type        = data.get('type', 'Single'),
            floor       = data.get('floor', 1),
            capacity    = data['capacity'],
            occupied    = 0,
            price       = data['price'],
            status      = 'Available',
            amenities   = data.get('amenities', '[]'),
            description = data.get('description', ''),
            image_url   = data.get('image_url', '')
        )
        db.session.add(room)
        db.session.commit()
        return ok({"room_id": room.room_id}, "Room added", 201)

    except Exception as e:
        db.session.rollback()
        return err(str(e), 500)


@app.route('/rooms/<int:room_id>', methods=['PUT'])
@jwt_required()
def update_room(room_id):
    """Admin. Body: any room fields to update."""
    try:
        room = Room.query.get(room_id)
        if not room:
            return err("Room not found", 404)

        data = request.json
        for field in ['room_no','block','type','floor','capacity','price','status','amenities','description','image_url']:
            if field in data:
                setattr(room, field, data[field])

        db.session.commit()
        return ok(msg="Room updated")

    except Exception as e:
        db.session.rollback()
        return err(str(e), 500)


@app.route('/rooms/<int:room_id>', methods=['DELETE'])
@jwt_required()
def delete_room(room_id):
    """Admin only."""
    try:
        room = Room.query.get(room_id)
        if not room:
            return err("Room not found", 404)
        db.session.delete(room)
        db.session.commit()
        return ok(msg="Room deleted")
    except Exception as e:
        db.session.rollback()
        return err(str(e), 500)


# =============================================================
#  ⑤ BOOKINGS  (warden approval workflow)
# =============================================================

@app.route('/bookings', methods=['GET'])
@jwt_required()
def get_bookings():
    """
    For warden/admin: all bookings.
    For student: their own bookings (pass ?student_id=X or uses JWT).
    Query param: status (Pending | Approved | Rejected)
    """
    try:
        uid     = current_user_id()
        user    = User.query.get(uid)
        query   = Booking.query

        if user.role == 'student':
            student = Student.query.filter_by(user_id=uid).first()
            if student:
                query = query.filter_by(student_id=student.student_id)

        if request.args.get('status'):
            query = query.filter_by(status=request.args['status'])

        bookings = query.order_by(Booking.requested_on.desc()).all()

        result = []
        for b in bookings:
            student = Student.query.get(b.student_id)
            user_rec = User.query.get(student.user_id) if student else None
            result.append({
                "booking_id":       b.booking_id,
                "student_id":       b.student_id,
                "student_name":     user_rec.name  if user_rec else "—",
                "room_id":          b.room_id,
                "full_name":        b.full_name,
                "room_type":        b.room_type,
                "preferred_block":  b.preferred_block,
                "checkin_date":     b.checkin_date,
                "duration":         b.duration,
                "notes":            b.notes,
                "status":           b.status,
                "rejection_reason": b.rejection_reason,
                "requested_on":     b.requested_on.strftime('%d %b %Y') if b.requested_on else "—",
                "approved_on":      b.approved_on.strftime('%d %b %Y')  if b.approved_on  else "—",
            })
        return ok(result)

    except Exception as e:
        return err(str(e), 500)


@app.route('/bookings', methods=['POST'])
@jwt_required()
def create_booking():
    """
    Student submits a booking request (matches frontend Rooms.submit()).
    Body: { full_name, room_type, preferred_block, checkin_date, duration, notes?, room_id? }
    """
    try:
        uid     = current_user_id()
        data    = request.json
        student = Student.query.filter_by(user_id=uid).first()

        if not student:
            return err("Student record not found", 404)

        booking = Booking(
            student_id      = student.student_id,
            room_id         = data.get('room_id'),
            full_name       = data.get('full_name', ''),
            room_type       = data.get('room_type', ''),
            preferred_block = data.get('preferred_block', ''),
            checkin_date    = data.get('checkin_date', ''),
            duration        = data.get('duration', ''),
            notes           = data.get('notes', ''),
            status          = 'Pending'
        )
        db.session.add(booking)
        db.session.commit()

        # Notify student
        notif = Notification(
            user_id = uid,
            title   = "Booking Request Submitted",
            message = f"Your room booking request (#{booking.booking_id}) is pending warden approval.",
            type    = "info"
        )
        db.session.add(notif)
        db.session.commit()

        return ok({"booking_id": booking.booking_id}, "Booking request submitted", 201)

    except Exception as e:
        db.session.rollback()
        return err(str(e), 500)


@app.route('/bookings/<int:booking_id>', methods=['PUT'])
@jwt_required()
def update_booking(booking_id):
    """
    Warden/Admin approves or rejects.
    Body: { status: "Approved"|"Rejected", rejection_reason? }
    """
    try:
        uid     = current_user_id()
        data    = request.json
        booking = Booking.query.get(booking_id)

        if not booking:
            return err("Booking not found", 404)

        new_status = data.get('status')
        booking.status      = new_status
        booking.approved_by = uid
        booking.approved_on = datetime.utcnow()

        if new_status == 'Rejected':
            booking.rejection_reason = data.get('rejection_reason', '')

        if new_status == 'Approved' and booking.room_id:
            # Assign room to student
            room    = Room.query.get(booking.room_id)
            student = Student.query.get(booking.student_id)
            if room and student and room.occupied < room.capacity:
                room.occupied  += 1
                student.room_id = room.room_id
                if room.occupied >= room.capacity:
                    room.status = 'Occupied'

        db.session.commit()

        # Notify the student
        student_user = None
        student = Student.query.get(booking.student_id)
        if student:
            student_user = User.query.get(student.user_id)

        if student_user:
            notif = Notification(
                user_id = student_user.user_id,
                title   = f"Booking {new_status}",
                message = (
                    f"Your room booking (#{booking_id}) has been {new_status.lower()}."
                    + (f" Reason: {booking.rejection_reason}" if new_status == 'Rejected' else "")
                ),
                type    = "success" if new_status == "Approved" else "error"
            )
            db.session.add(notif)
            db.session.commit()

        return ok(msg=f"Booking {new_status}")

    except Exception as e:
        db.session.rollback()
        return err(str(e), 500)


@app.route('/bookings/<int:booking_id>/cancel', methods=['PUT'])
@jwt_required()
def cancel_booking(booking_id):
    """Student cancels their own pending booking."""
    try:
        booking = Booking.query.get(booking_id)
        if not booking:
            return err("Booking not found", 404)

        booking.status = 'Cancelled'

        # Free up room if it was approved
        if booking.room_id:
            room = Room.query.get(booking.room_id)
            student = Student.query.get(booking.student_id)
            if room and room.occupied > 0:
                room.occupied -= 1
            if student:
                student.room_id = None
            if room and room.status == 'Occupied':
                room.status = 'Available'

        db.session.commit()
        return ok(msg="Booking cancelled")

    except Exception as e:
        db.session.rollback()
        return err(str(e), 500)


# =============================================================
#  ⑥ COMPLAINTS
# =============================================================

@app.route('/complaints', methods=['GET'])
@jwt_required()
def get_complaints():
    """
    Admin/Warden/Maintenance: all complaints.
    Student: only their own.
    """
    try:
        uid   = current_user_id()
        user  = User.query.get(uid)
        query = Complaint.query

        if user.role == 'student':
            student = Student.query.filter_by(user_id=uid).first()
            if student:
                query = query.filter_by(student_id=student.student_id)

        if request.args.get('status'):
            query = query.filter_by(status=request.args['status'])
        if request.args.get('priority'):
            query = query.filter_by(priority=request.args['priority'])

        complaints = query.order_by(Complaint.created_at.desc()).all()

        result = []
        for c in complaints:
            student  = Student.query.get(c.student_id)
            user_rec = User.query.get(student.user_id) if student else None
            room     = Room.query.get(student.room_id) if student else None
            result.append({
                "complaint_id": c.complaint_id,
                "id":           f"CMP-{str(c.complaint_id).zfill(3)}",   # CMP-001 format
                "student_id":   c.student_id,
                "name":         user_rec.name if user_rec else "—",
                "room":         room.room_no  if room     else "—",
                "cat":          c.category,
                "sub":          c.subject,
                "desc":         c.description,
                "pri":          c.priority,
                "status":       c.status,
                "steps":        {"Pending": 1, "In Progress": 2, "Resolved": 3}.get(c.status, 1),
                "created_at":   c.created_at.strftime('%d %b %Y') if c.created_at else "—",
            })
        return ok(result)

    except Exception as e:
        return err(str(e), 500)


@app.route('/complaints', methods=['POST'])
@jwt_required()
def create_complaint():
    """
    Matches frontend Comps.submit().
    Body: { category, subject, description, priority }
    """
    try:
        uid     = current_user_id()
        data    = request.json
        student = Student.query.filter_by(user_id=uid).first()

        if not student:
            return err("Student record not found", 404)

        comp = Complaint(
            student_id  = student.student_id,
            category    = data.get('category', 'Other'),
            subject     = data.get('subject', ''),
            description = data.get('description', ''),
            priority    = data.get('priority', 'Medium'),
            status      = 'Pending'
        )
        db.session.add(comp)
        db.session.commit()

        return ok({"complaint_id": comp.complaint_id}, "Complaint submitted", 201)

    except Exception as e:
        db.session.rollback()
        return err(str(e), 500)


@app.route('/complaints/<int:complaint_id>', methods=['PUT'])
@jwt_required()
def update_complaint(complaint_id):
    """
    Warden/Admin/Maintenance updates status.
    Body: { status: "In Progress"|"Resolved", assigned_to? }
    """
    try:
        data = request.json
        comp = Complaint.query.get(complaint_id)
        if not comp:
            return err("Complaint not found", 404)

        if 'status'      in data: comp.status      = data['status']
        if 'assigned_to' in data: comp.assigned_to = data['assigned_to']
        comp.updated_at = datetime.utcnow()

        db.session.commit()
        return ok(msg=f"Complaint updated to {comp.status}")

    except Exception as e:
        db.session.rollback()
        return err(str(e), 500)


# =============================================================
#  ⑦ LEAVES
# =============================================================

@app.route('/leaves', methods=['GET'])
@jwt_required()
def get_leaves():
    try:
        uid   = current_user_id()
        user  = User.query.get(uid)
        query = Leave.query

        if user.role == 'student':
            student = Student.query.filter_by(user_id=uid).first()
            if student:
                query = query.filter_by(student_id=student.student_id)

        leaves = query.order_by(Leave.created_at.desc()).all()

        result = []
        for l in leaves:
            student  = Student.query.get(l.student_id)
            user_rec = User.query.get(student.user_id) if student else None
            room     = Room.query.get(student.room_id) if student else None
            icons    = {'Home Visit':'🏠','Medical':'🏥','Event':'🎉','Other':'📝'}
            result.append({
                "leave_id":   l.leave_id,
                "student_id": l.student_id,
                "name":       user_rec.name if user_rec else "—",
                "room":       room.room_no  if room     else "—",
                "type":       l.type,
                "from":       l.from_date,
                "to":         l.to_date,
                "reason":     l.reason,
                "status":     l.status,
                "icon":       icons.get(l.type, '📝'),
                "created_at": l.created_at.strftime('%d %b %Y') if l.created_at else "—",
            })
        return ok(result)

    except Exception as e:
        return err(str(e), 500)


@app.route('/leaves', methods=['POST'])
@jwt_required()
def create_leave():
    """Body: { type, from_date, to_date, reason }"""
    try:
        uid     = current_user_id()
        data    = request.json
        student = Student.query.filter_by(user_id=uid).first()

        if not student:
            return err("Student record not found", 404)

        leave = Leave(
            student_id = student.student_id,
            type       = data.get('type', 'Home Visit'),
            from_date  = data.get('from_date', ''),
            to_date    = data.get('to_date', ''),
            reason     = data.get('reason', ''),
            status     = 'Pending'
        )
        db.session.add(leave)
        db.session.commit()
        return ok({"leave_id": leave.leave_id}, "Leave application submitted", 201)

    except Exception as e:
        db.session.rollback()
        return err(str(e), 500)


@app.route('/leaves/<int:leave_id>', methods=['PUT'])
@jwt_required()
def update_leave(leave_id):
    """Warden approves/rejects. Body: { status: "Approved"|"Rejected" }"""
    try:
        uid   = current_user_id()
        data  = request.json
        leave = Leave.query.get(leave_id)
        if not leave:
            return err("Leave not found", 404)

        leave.status      = data.get('status', leave.status)
        leave.approved_by = uid
        db.session.commit()
        return ok(msg=f"Leave {leave.status}")

    except Exception as e:
        db.session.rollback()
        return err(str(e), 500)


# =============================================================
#  ⑧ PAYMENTS
# =============================================================

@app.route('/payments', methods=['GET'])
@jwt_required()
def get_payments():
    """
    Student: own payments.
    Admin/Warden: all — matches frontend Admin.renderPayments().
    """
    try:
        uid   = current_user_id()
        user  = User.query.get(uid)
        query = Payment.query

        if user.role == 'student':
            student = Student.query.filter_by(user_id=uid).first()
            if student:
                query = query.filter_by(student_id=student.student_id)

        payments = query.order_by(Payment.created_at.desc()).all()

        result = []
        for p in payments:
            student  = Student.query.get(p.student_id)
            user_rec = User.query.get(student.user_id) if student else None
            room     = Room.query.get(student.room_id) if student else None
            result.append({
                "payment_id": p.payment_id,
                "student_id": p.student_id,
                "name":       user_rec.name if user_rec else "—",
                "room":       room.room_no  if room     else "—",
                "month":      p.month,
                "amount":     p.amount,
                "due":        p.due_date,
                "paid":       p.paid_date or "—",
                "method":     p.method or "—",
                "status":     p.status,
            })
        return ok(result)

    except Exception as e:
        return err(str(e), 500)


@app.route('/payments/<int:payment_id>/pay', methods=['PUT'])
@jwt_required()
def make_payment(payment_id):
    """
    Marks a payment as Paid. Body: { method: "UPI"|"Card"|"Net Banking"|"Cash" }
    Matches frontend Fees.pay() and Admin.collectFee().
    """
    try:
        data    = request.json
        payment = Payment.query.get(payment_id)
        if not payment:
            return err("Payment not found", 404)

        payment.status    = 'Paid'
        payment.paid_date = datetime.utcnow().strftime('%d %b %Y')
        payment.method    = data.get('method', 'UPI')
        db.session.commit()

        txn_id = f"TXN{payment_id}{int(datetime.utcnow().timestamp())}"[-10:]
        return ok({"txn_id": txn_id}, "Payment successful")

    except Exception as e:
        db.session.rollback()
        return err(str(e), 500)


# =============================================================
#  ⑨ FINES
# =============================================================

@app.route('/fines', methods=['GET'])
@jwt_required()
def get_fines():
    try:
        uid   = current_user_id()
        user  = User.query.get(uid)
        query = Fine.query

        if user.role == 'student':
            student = Student.query.filter_by(user_id=uid).first()
            if student:
                query = query.filter_by(student_id=student.student_id)

        fines = query.order_by(Fine.issued_on.desc()).all()
        return ok([{
            "fine_id":    f.fine_id,
            "student_id": f.student_id,
            "title":      f.title,
            "amount":     f.amount,
            "reason":     f.reason,
            "status":     f.status,
            "issued_on":  f.issued_on.strftime('%d %b %Y') if f.issued_on else "—",
            "paid_on":    f.paid_on.strftime('%d %b %Y')   if f.paid_on   else "—",
        } for f in fines])

    except Exception as e:
        return err(str(e), 500)


@app.route('/fines', methods=['POST'])
@jwt_required()
def create_fine():
    """Admin. Body: { student_id, title, amount, reason }"""
    try:
        data = request.json
        fine = Fine(
            student_id = data['student_id'],
            title      = data['title'],
            amount     = data['amount'],
            reason     = data.get('reason', ''),
            status     = 'Unpaid'
        )
        db.session.add(fine)
        db.session.commit()
        return ok({"fine_id": fine.fine_id}, "Fine issued", 201)

    except Exception as e:
        db.session.rollback()
        return err(str(e), 500)


@app.route('/fines/<int:fine_id>/pay', methods=['PUT'])
@jwt_required()
def pay_fine(fine_id):
    """Student pays a fine. Matches frontend Fees.payFine()."""
    try:
        fine = Fine.query.get(fine_id)
        if not fine:
            return err("Fine not found", 404)
        fine.status  = 'Paid'
        fine.paid_on = datetime.utcnow()
        db.session.commit()
        return ok(msg="Fine paid")
    except Exception as e:
        db.session.rollback()
        return err(str(e), 500)


# =============================================================
#  ⑩ MAINTENANCE
# =============================================================

@app.route('/maintenance', methods=['GET'])
@jwt_required()
def get_maintenance():
    try:
        tasks = Maintenance.query.order_by(Maintenance.created_at.desc()).all()
        return ok([{
            "maintenance_id": m.maintenance_id,
            "room_id":        m.room_id,
            "issue":          m.issue,
            "description":    m.description,
            "status":         m.status,
            "assigned_to":    m.assigned_to,
            "created_at":     m.created_at.strftime('%d %b %Y') if m.created_at else "—",
        } for m in tasks])
    except Exception as e:
        return err(str(e), 500)


@app.route('/maintenance', methods=['POST'])
@jwt_required()
def create_maintenance():
    """Body: { room_id, issue, description }"""
    try:
        uid  = current_user_id()
        data = request.json
        task = Maintenance(
            room_id     = data['room_id'],
            reported_by = uid,
            issue       = data['issue'],
            description = data.get('description', ''),
            status      = 'Pending'
        )
        db.session.add(task)
        db.session.commit()
        return ok({"maintenance_id": task.maintenance_id}, "Maintenance request created", 201)

    except Exception as e:
        db.session.rollback()
        return err(str(e), 500)


@app.route('/maintenance/<int:mid>', methods=['PUT'])
@jwt_required()
def update_maintenance(mid):
    """Body: { status, assigned_to? }"""
    try:
        uid  = current_user_id()
        data = request.json
        task = Maintenance.query.get(mid)
        if not task:
            return err("Task not found", 404)
        if 'status'      in data: task.status      = data['status']
        if 'assigned_to' in data: task.assigned_to = data['assigned_to']
        db.session.commit()
        return ok(msg="Maintenance updated")
    except Exception as e:
        db.session.rollback()
        return err(str(e), 500)


# =============================================================
#  ⑪ ATTENDANCE
# =============================================================

@app.route('/attendance', methods=['GET'])
@jwt_required()
def get_attendance():
    """Query params: student_id, date"""
    try:
        query = Attendance.query
        if request.args.get('student_id'):
            query = query.filter_by(student_id=int(request.args['student_id']))
        if request.args.get('date'):
            query = query.filter_by(date=request.args['date'])

        records = query.all()
        return ok([{
            "attendance_id": a.attendance_id,
            "student_id":    a.student_id,
            "date":          a.date,
            "status":        a.status,
        } for a in records])

    except Exception as e:
        return err(str(e), 500)


@app.route('/attendance', methods=['POST'])
@jwt_required()
def mark_attendance():
    """Body: { student_id, date, status }"""
    try:
        data = request.json
        rec  = Attendance(
            student_id = data['student_id'],
            date       = data['date'],
            status     = data.get('status', 'Present')
        )
        db.session.add(rec)
        db.session.commit()
        return ok({"attendance_id": rec.attendance_id}, "Attendance marked", 201)

    except Exception as e:
        db.session.rollback()
        return err(str(e), 500)


# =============================================================
#  ⑫ NOTIFICATIONS
# =============================================================

@app.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """
    Returns notifications for current user + all broadcasts (user_id IS NULL).
    Matches frontend Topbar notification dropdown.
    """
    try:
        uid = current_user_id()
        notifications = Notification.query.filter(
            (Notification.user_id == uid) | (Notification.user_id == None)
        ).order_by(Notification.created_at.desc()).limit(20).all()

        return ok([{
            "notification_id": n.notification_id,
            "title":           n.title,
            "message":         n.message,
            "type":            n.type,
            "is_read":         n.is_read,
            "unread":          not n.is_read,   # alias for frontend compatibility
            "created_at":      n.created_at.strftime('%d %b %Y, %I:%M %p') if n.created_at else "—",
        } for n in notifications])

    except Exception as e:
        return err(str(e), 500)


@app.route('/notifications/<int:nid>/read', methods=['PUT'])
@jwt_required()
def mark_notification_read(nid):
    """Matches frontend Topbar.readOne()."""
    try:
        notif = Notification.query.get(nid)
        if notif:
            notif.is_read = True
            db.session.commit()
        return ok(msg="Marked as read")
    except Exception as e:
        db.session.rollback()
        return err(str(e), 500)


@app.route('/notifications/read-all', methods=['PUT'])
@jwt_required()
def mark_all_read():
    """Matches frontend Topbar.readAll()."""
    try:
        uid = current_user_id()
        Notification.query.filter_by(user_id=uid, is_read=False).update({"is_read": True})
        db.session.commit()
        return ok(msg="All notifications marked as read")
    except Exception as e:
        db.session.rollback()
        return err(str(e), 500)


@app.route('/notifications', methods=['POST'])
@jwt_required()
def create_notification():
    """Admin broadcasts. Body: { title, message, type, user_id? }"""
    try:
        data  = request.json
        notif = Notification(
            user_id = data.get('user_id'),   # None = broadcast
            title   = data['title'],
            message = data['message'],
            type    = data.get('type', 'info')
        )
        db.session.add(notif)
        db.session.commit()
        return ok({"notification_id": notif.notification_id}, "Notification sent", 201)

    except Exception as e:
        db.session.rollback()
        return err(str(e), 500)


# =============================================================
#  ⑬ VISITORS
# =============================================================

@app.route('/visitors', methods=['GET'])
@jwt_required()
def get_visitors():
    """Warden/Admin: all visitors. Matches frontend live ticker."""
    try:
        visitors = Visitor.query.order_by(Visitor.checked_in_at.desc()).all()
        return ok([{
            "visitor_id":      v.visitor_id,
            "student_id":      v.student_id,
            "visitor_name":    v.visitor_name,
            "relation":        v.relation,
            "phone":           v.phone,
            "id_proof_type":   v.id_proof_type,
            "purpose":         v.purpose,
            "checked_in_at":   v.checked_in_at.strftime('%d %b %Y, %I:%M %p')  if v.checked_in_at  else "—",
            "checked_out_at":  v.checked_out_at.strftime('%d %b %Y, %I:%M %p') if v.checked_out_at else "—",
            "status":          v.status,
        } for v in visitors])
    except Exception as e:
        return err(str(e), 500)


@app.route('/visitors', methods=['POST'])
@jwt_required()
def checkin_visitor():
    """Warden logs a visitor check-in. Body: { student_id, visitor_name, relation, phone, id_proof_type, purpose }"""
    try:
        uid  = current_user_id()
        data = request.json
        v    = Visitor(
            student_id      = data['student_id'],
            visitor_name    = data['visitor_name'],
            relation        = data.get('relation', ''),
            phone           = data.get('phone', ''),
            id_proof_type   = data.get('id_proof_type', ''),
            id_proof_number = data.get('id_proof_number', ''),
            purpose         = data.get('purpose', ''),
            approved_by     = uid,
            status          = 'Checked In'
        )
        db.session.add(v)
        db.session.commit()
        return ok({"visitor_id": v.visitor_id}, "Visitor checked in", 201)

    except Exception as e:
        db.session.rollback()
        return err(str(e), 500)


@app.route('/visitors/<int:visitor_id>/checkout', methods=['PUT'])
@jwt_required()
def checkout_visitor(visitor_id):
    """Warden marks checkout."""
    try:
        v = Visitor.query.get(visitor_id)
        if not v:
            return err("Visitor record not found", 404)
        v.checked_out_at = datetime.utcnow()
        v.status         = 'Checked Out'
        db.session.commit()
        return ok(msg="Visitor checked out")
    except Exception as e:
        db.session.rollback()
        return err(str(e), 500)


# =============================================================
#  ⑭ STUDENTS LIST  (Admin / Warden)
# =============================================================

@app.route('/students', methods=['GET'])
@jwt_required()
def get_students():
    """Returns enriched student list for admin tables."""
    try:
        students = Student.query.all()
        result = []
        for s in students:
            user = User.query.get(s.user_id)
            room = Room.query.get(s.room_id) if s.room_id else None
            result.append({
                "student_id": s.student_id,
                "user_id":    s.user_id,
                "name":       user.name  if user else "—",
                "email":      user.email if user else "—",
                "staff_id":   user.staff_id if user else "—",
                "room_id":    s.room_id,
                "room_no":    room.room_no if room else "Not Assigned",
                "block":      room.block   if room else "—",
                "course":     s.course,
                "year":       s.year,
            })
        return ok(result)
    except Exception as e:
        return err(str(e), 500)


@app.route('/students/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student(student_id):
    try:
        s    = Student.query.get(student_id)
        if not s:
            return err("Student not found", 404)
        user = User.query.get(s.user_id)
        room = Room.query.get(s.room_id) if s.room_id else None
        return ok({
            "student_id": s.student_id,
            "name":       user.name  if user else "—",
            "email":      user.email if user else "—",
            "course":     s.course,
            "year":       s.year,
            "room_id":    s.room_id,
            "room_no":    room.room_no if room else "Not Assigned",
        })
    except Exception as e:
        return err(str(e), 500)


# =============================================================
#  ⑮ ADMIN DASHBOARD STATS
# =============================================================

@app.route('/admin/stats', methods=['GET'])
@jwt_required()
def admin_stats():
    """
    Returns summary numbers for the Admin dashboard stat cards.
    Replaces the hardcoded numbers scattered in Pages._map.
    """
    try:
        total_rooms     = Room.query.count()
        available_rooms = Room.query.filter_by(status='Available').count()
        total_students  = Student.query.count()
        total_capacity  = db.session.query(db.func.sum(Room.capacity)).scalar() or 0
        total_occupied  = db.session.query(db.func.sum(Room.occupied)).scalar() or 0
        occupancy_pct   = round((total_occupied / total_capacity * 100), 1) if total_capacity else 0

        pending_bookings   = Booking.query.filter_by(status='Pending').count()
        open_complaints    = Complaint.query.filter_by(status='Pending').count()
        inprog_complaints  = Complaint.query.filter_by(status='In Progress').count()
        resolved_complaints= Complaint.query.filter_by(status='Resolved').count()

        unpaid_fees   = Payment.query.filter_by(status='Pending').count()
        overdue_fees  = Payment.query.filter_by(status='Overdue').count()
        total_collected = db.session.query(db.func.sum(Payment.amount)).filter_by(status='Paid').scalar() or 0
        total_pending_amt = db.session.query(db.func.sum(Payment.amount)).filter_by(status='Pending').scalar() or 0

        pending_leaves = Leave.query.filter_by(status='Pending').count()
        active_visitors= Visitor.query.filter_by(status='Checked In').count()

        return ok({
            "rooms": {
                "total":     total_rooms,
                "available": available_rooms,
                "occupied":  total_rooms - available_rooms,
            },
            "occupancy": {
                "total_beds":  total_capacity,
                "occupied":    total_occupied,
                "vacant":      total_capacity - total_occupied,
                "percentage":  occupancy_pct,
            },
            "students":         total_students,
            "pending_bookings": pending_bookings,
            "complaints": {
                "open":     open_complaints,
                "in_progress": inprog_complaints,
                "resolved": resolved_complaints,
            },
            "payments": {
                "collected":    total_collected,
                "pending_count": unpaid_fees,
                "overdue_count": overdue_fees,
                "pending_amount": total_pending_amt,
            },
            "pending_leaves":  pending_leaves,
            "active_visitors": active_visitors,
        })

    except Exception as e:
        return err(str(e), 500)


# =============================================================
#  RUN
# =============================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ All tables created / verified")
    app.run(debug=True, port=5000)