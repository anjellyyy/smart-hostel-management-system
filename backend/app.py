from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import Config
from chatbot import chatbot
from datetime import datetime
from werkzeug.exceptions import HTTPException

# ----------------- Flask App Setup -----------------
app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "*"}})

# ----------------- Configuration -----------------
app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = Config.SECRET_KEY

db = SQLAlchemy(app)

# ----------------- Models -----------------
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='user')


class Student(db.Model):
    __tablename__ = 'students'
    student_id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    room_no = db.Column(db.String(10), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Room(db.Model):
    __tablename__ = 'rooms'
    room_no = db.Column(db.String(10), primary_key=True)
    type = db.Column(db.String(20), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    availability = db.Column(db.String(20), default='Available')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Payment(db.Model):
    __tablename__ = 'payments'
    payment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    payment_type = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), default='Completed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Complaint(db.Model):
    __tablename__ = 'complaints'
    complaint_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(20), nullable=False)
    issue_type = db.Column(db.String(30), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    complaint_date = db.Column(db.DateTime, default=datetime.utcnow)


# ----------------- Helper -----------------
def get_room_availability():
    rooms = Room.query.all()
    result = []
    for room in rooms:
        student = Student.query.filter_by(room_no=room.room_no).first()
        status = 'Available' if not student else 'Occupied'
        occupied_by = student.name if student else None
        result.append({
            'room_no': room.room_no,
            'type': room.type,
            'capacity': room.capacity,
            'availability': status,
            'occupied_by': occupied_by
        })
    return result


# ----------------- Routes -----------------
@app.route('/')
def home():
    return jsonify({
        "message": "Hostel Management API is running ✅",
        "endpoints": [
            "/api/dashboard", "/api/students", "/api/rooms",
            "/api/payments", "/api/complaints", "/api/chatbot"
        ]
    })


# ----------------- Dashboard -----------------
@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    total_students = Student.query.count()
    total_rooms = Room.query.count()
    available_rooms = len([r for r in get_room_availability() if r['availability'] == 'Available'])
    pending_complaints = Complaint.query.filter_by(status='Pending').count()
    return jsonify({
        'totalStudents': total_students,
        'totalRooms': total_rooms,
        'availableRooms': available_rooms,
        'pendingComplaints': pending_complaints
    })


# ----------------- Recent Activities -----------------
@app.route('/api/activities', methods=['GET'])
def get_activities():
    try:
        recent_students = Student.query.order_by(Student.created_at.desc()).limit(3).all()
        recent_payments = Payment.query.order_by(Payment.created_at.desc()).limit(3).all()
        recent_complaints = Complaint.query.order_by(Complaint.complaint_date.desc()).limit(3).all()

        activities = []
        for s in recent_students:
            activities.append({
                'type': 'registration',
                'title': 'New Student Registration',
                'description': f'Student {s.student_id} registered',
                'date': s.created_at.strftime('%Y-%m-%d')
            })
        for p in recent_payments:
            activities.append({
                'type': 'payment',
                'title': 'Payment Received',
                'description': f'Payment of ₹{p.amount} recorded for student {p.student_id}',
                'date': p.created_at.strftime('%Y-%m-%d')
            })
        for c in recent_complaints:
            activities.append({
                'type': 'complaint',
                'title': 'New Complaint Filed',
                'description': f'Complaint filed by student {c.student_id}',
                'date': c.complaint_date.strftime('%Y-%m-%d')
            })
        activities.sort(key=lambda x: x['date'], reverse=True)
        return jsonify(activities[:5])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ----------------- Students -----------------
@app.route('/api/students', methods=['GET', 'POST'])
def handle_students():
    if request.method == 'GET':
        students = Student.query.all()
        return jsonify([{
            'student_id': s.student_id,
            'name': s.name,
            'age': s.age,
            'gender': s.gender,
            'contact': s.contact,
            'room_no': s.room_no
        } for s in students])
    else:
        data = request.get_json()
        if not data or not all(k in data for k in ['student_id', 'name', 'age', 'gender', 'contact']):
            return jsonify({'error': 'Missing required fields'}), 400
        student = Student(**data)
        db.session.add(student)
        db.session.commit()
        return jsonify({'message': 'Student added successfully'})


# ----------------- Rooms -----------------
@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    return jsonify(get_room_availability())


@app.route('/api/rooms/available', methods=['GET'])
def get_available_rooms():
    rooms = Room.query.all()
    available = [r for r in rooms if not Student.query.filter_by(room_no=r.room_no).first()]
    return jsonify([{
        'room_no': r.room_no,
        'type': r.type,
        'capacity': r.capacity
    } for r in available])


@app.route('/api/rooms/allocate', methods=['POST'])
def allocate_room():
    data = request.get_json()
    student_id = data.get('student_id')
    room_no = data.get('room_no')

    student = Student.query.filter_by(student_id=student_id).first()
    room = Room.query.filter_by(room_no=room_no).first()

    if not student or not room:
        return jsonify({'error': 'Invalid student or room'}), 400

    student.room_no = room_no
    db.session.commit()
    return jsonify({'message': f'Room {room_no} allocated to {student_id}'})


@app.route('/api/rooms/vacate', methods=['POST'])
def vacate_room():
    data = request.get_json()
    room_no = data.get('room_no')

    student = Student.query.filter_by(room_no=room_no).first()
    if not student:
        return jsonify({'error': 'No student assigned to this room'}), 400

    student.room_no = None
    db.session.commit()
    return jsonify({'message': f'Room {room_no} vacated'})


# ----------------- Payments -----------------
@app.route('/api/payments', methods=['GET', 'POST'])
def handle_payments():
    if request.method == 'GET':
        payments = Payment.query.all()
        return jsonify([{
            'payment_id': p.payment_id,
            'student_id': p.student_id,
            'amount': f'₹{p.amount:.2f}',
            'payment_date': p.payment_date.isoformat(),
            'payment_type': p.payment_type,
            'status': p.status
        } for p in payments])
    else:
        data = request.get_json()
        if not data or not all(k in data for k in ['student_id', 'amount', 'payment_date', 'payment_type']):
            return jsonify({'error': 'Missing required fields'}), 400
        try:
            payment_date = datetime.strptime(data['payment_date'], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({'error': 'Invalid date format, expected YYYY-MM-DD'}), 400
        payment = Payment(
            student_id=data['student_id'],
            amount=data['amount'],
            payment_date=payment_date,
            payment_type=data['payment_type']
        )
        db.session.add(payment)
        db.session.commit()
        return jsonify({'message': 'Payment recorded successfully'})


# ----------------- Complaints -----------------
@app.route('/api/complaints', methods=['GET', 'POST'])
def handle_complaints():
    if request.method == 'GET':
        complaints = Complaint.query.all()
        return jsonify([{
            'complaint_id': c.complaint_id,
            'student_id': c.student_id,
            'issue_type': c.issue_type,
            'description': c.description,
            'status': c.status,
            'complaint_date': c.complaint_date.isoformat()
        } for c in complaints])
    else:
        data = request.get_json()
        if not data or not all(k in data for k in ['student_id', 'issue_type', 'description']):
            return jsonify({'error': 'Missing required fields'}), 400
        complaint = Complaint(
            student_id=data['student_id'],
            issue_type=data['issue_type'],
            description=data['description']
        )
        db.session.add(complaint)
        db.session.commit()
        return jsonify({'message': 'Complaint submitted successfully'})


@app.route('/api/complaints/<int:complaint_id>/resolve', methods=['POST'])
def resolve_complaint(complaint_id):
    complaint = Complaint.query.get(complaint_id)
    if not complaint:
        return jsonify({'error': 'Complaint not found'}), 404
    complaint.status = 'Resolved'
    db.session.commit()
    return jsonify({'message': 'Complaint marked as resolved'})


# ----------------- Auth -----------------
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = (data or {}).get('username')
    email = (data or {}).get('email')
    password = (data or {}).get('password')
    if not username or not email or not password:
        return jsonify({'error': 'All fields are required'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400
    user = User(username=username, email=email, password=password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'success': True, 'message': 'User registered successfully'})


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = (data or {}).get('username')
    password = (data or {}).get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    user = User.query.filter_by(username=username, password=password).first()
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    return jsonify({'success': True, 'message': 'Login successful', 'user': {'username': user.username, 'role': user.role}})


@app.route('/api/logout', methods=['POST'])
def logout():
    return jsonify({'success': True, 'message': 'Logged out successfully'})


# ----------------- Chatbot -----------------
@app.route('/api/chatbot', methods=['POST'])
def handle_chatbot():
    data = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    response = chatbot.get_response(message)
    return jsonify({'reply': response})


# ----------------- Error Handling -----------------
@app.errorhandler(HTTPException)
def handle_http_exception(e: HTTPException):
    response = {
        'error': e.name,
        'message': e.description,
        'status': e.code
    }
    return jsonify(response), e.code


@app.errorhandler(Exception)
def handle_exception(e: Exception):
    print(f"Unhandled error: {e}")
    return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}), 500


# ----------------- Main -----------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        if Room.query.count() == 0:
            rooms = [
                Room(room_no='101', type='Single', capacity=1),
                Room(room_no='102', type='Double', capacity=2),
                Room(room_no='103', type='Single', capacity=1),
                Room(room_no='201', type='Suite', capacity=3)
            ]
            db.session.add_all(rooms)
            db.session.commit()

        if Student.query.count() == 0:
            students = [
                Student(student_id='S1001', name='John Doe', age=20, gender='Male', contact='+911234567890', room_no='101'),
                Student(student_id='S1002', name='Jane Smith', age=21, gender='Female', contact='+911234567891', room_no='102')
            ]
            db.session.add_all(students)
            db.session.commit()

        if Complaint.query.count() == 0:
            db.session.add(Complaint(student_id='S1002', issue_type='Plumbing', description='Leak in bathroom', status='Pending'))
            db.session.commit()

    print("✅ Server running at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
