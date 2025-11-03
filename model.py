from database import db
from datetime import datetime

class Student:
    @staticmethod
    def get_all():
        query = "SELECT * FROM students ORDER BY student_id"
        return db.execute_query(query)

    @staticmethod
    def get_by_id(student_id):
        query = "SELECT * FROM students WHERE student_id = %s"
        return db.execute_query(query, (student_id,))

    @staticmethod
    def create(student_data):
        query = """
        INSERT INTO students (student_id, name, age, gender, contact, room_no)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (
            student_data['student_id'],
            student_data['name'],
            student_data['age'],
            student_data['gender'],
            student_data['contact'],
            student_data['room_no']
        )
        return db.execute_query(query, params)

    @staticmethod
    def update_room(student_id, room_no):
        query = "UPDATE students SET room_no = %s WHERE student_id = %s"
        return db.execute_query(query, (room_no, student_id))

    @staticmethod
    def clear_room_by_room_no(room_no):
        query = "UPDATE students SET room_no = NULL WHERE room_no = %s"
        return db.execute_query(query, (room_no,))

    @staticmethod
    def delete(student_id):
        query = "DELETE FROM students WHERE student_id = %s"
        return db.execute_query(query, (student_id,))

    @staticmethod
    def update(student_id, data):
        fields = []
        params = []
        allowed = ['name', 'age', 'gender', 'contact', 'room_no']
        for key in allowed:
            if key in data:
                fields.append(f"{key} = %s")
                params.append(data[key])
        if not fields:
            return 0
        params.append(student_id)
        query = f"UPDATE students SET {', '.join(fields)} WHERE student_id = %s"
        return db.execute_query(query, tuple(params))

class Room:
    @staticmethod
    def get_all():
        query = """
        SELECT 
            r.room_no,
            r.type,
            r.capacity,
            CASE WHEN s.student_id IS NULL THEN 'Available' ELSE 'Occupied' END AS availability,
            s.name AS occupied_by
        FROM rooms r 
        LEFT JOIN students s ON r.room_no = s.room_no
        ORDER BY r.room_no
        """
        return db.execute_query(query)

    @staticmethod
    def get_available():
        query = """
        SELECT r.* 
        FROM rooms r 
        LEFT JOIN students s ON r.room_no = s.room_no 
        WHERE s.student_id IS NULL
        """
        return db.execute_query(query)

    @staticmethod
    def update_availability(room_no, available):
        query = "UPDATE rooms SET availability = %s WHERE room_no = %s"
        status = "Available" if available else "Occupied"
        return db.execute_query(query, (status, room_no))

class Payment:
    @staticmethod
    def get_all():
        query = "SELECT * FROM payments ORDER BY payment_date DESC"
        return db.execute_query(query)

    @staticmethod
    def create(payment_data):
        query = """
        INSERT INTO payments (student_id, amount, payment_date, payment_type)
        VALUES (%s, %s, %s, %s)
        """
        params = (
            payment_data['student_id'],
            payment_data['amount'],
            payment_data['payment_date'],
            payment_data['payment_type']
        )
        return db.execute_query(query, params)

class Complaint:
    @staticmethod
    def get_all():
        query = """
        SELECT c.*, s.name as student_name 
        FROM complaints c 
        JOIN students s ON c.student_id = s.student_id 
        ORDER BY c.complaint_date DESC
        """
        return db.execute_query(query)

    @staticmethod
    def create(complaint_data):
        query = """
        INSERT INTO complaints (student_id, issue_type, description, status)
        VALUES (%s, %s, %s, 'Pending')
        """
        params = (
            complaint_data['student_id'],
            complaint_data['issue_type'],
            complaint_data['description']
        )
        return db.execute_query(query, params)

    @staticmethod
    def resolve(complaint_id):
        query = "UPDATE complaints SET status = 'Resolved' WHERE complaint_id = %s"
        return db.execute_query(query, (complaint_id,))

class Dashboard:
    @staticmethod
    def get_stats():
        # Compute stats using independent queries for reliability
        total_students = db.execute_query("SELECT COUNT(*) AS total_students FROM students")
        total_rooms = db.execute_query("SELECT COUNT(*) AS total_rooms FROM rooms")
        available_rooms = db.execute_query(
            """
            SELECT COUNT(*) AS available_rooms
            FROM rooms r
            LEFT JOIN students s ON r.room_no = s.room_no
            WHERE s.student_id IS NULL
            """
        )
        pending_complaints = db.execute_query(
            "SELECT COUNT(*) AS pending_complaints FROM complaints WHERE status = 'Pending'"
        )

        return {
            'total_students': (total_students[0]['total_students'] if total_students else 0) or 0,
            'total_rooms': (total_rooms[0]['total_rooms'] if total_rooms else 0) or 0,
            'available_rooms': (available_rooms[0]['available_rooms'] if available_rooms else 0) or 0,
            'pending_complaints': (pending_complaints[0]['pending_complaints'] if pending_complaints else 0) or 0
        }

    @staticmethod
    def get_recent_activities():
        # This would typically query an activities table
        # For now, return mock data
        return [
            {
                'type': 'registration',
                'title': 'New Student Registration',
                'description': 'Student S1001 registered',
                'date': '2023-10-15'
            },
            {
                'type': 'payment',
                'title': 'Payment Received',
                'description': 'Payment recorded for student S1002',
                'date': '2023-10-14'
            },
            {
                'type': 'complaint',
                'title': 'New Complaint Filed',
                'description': 'Complaint filed by student S1003',
                'date': '2023-10-13'
            }
        ]