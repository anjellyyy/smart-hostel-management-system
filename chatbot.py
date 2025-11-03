class Chatbot:
    def __init__(self):
        # No external API required for elementary chatbot
        pass

    def get_response(self, message):
        message_lower = (message or '').strip().lower()
        if not message_lower:
            return "Please type a message."

        # Simple intent-based responses
        if any(k in message_lower for k in ['hello', 'hi', 'hey']):
            return "Hello! I can help with rooms, students, payments, and complaints."

        if any(k in message_lower for k in ['room', 'availability', 'vacant']):
            return "Check Rooms section for availability. Use Allocate/Vacate to manage rooms."

        if any(k in message_lower for k in ['student', 'register', 'admission']):
            return "Go to Students to register a new student and assign a room."

        if any(k in message_lower for k in ['payment', 'fees', 'fee', 'due']):
            return "Use Payments to record fees. Accepted types: Semester Fee, Security Deposit, Other."

        if any(k in message_lower for k in ['complaint', 'issue', 'problem', 'support']):
            return "Use Complaints to file and resolve issues. Typical SLA: 24-48 hours."

        if any(k in message_lower for k in ['contact', 'phone', 'email']):
            return "Hostel office: +1 234 567 8900, email: hostel@university.edu (9am-5pm)."

        return "I can help with: students, rooms, payments, complaints. Try asking about one of these."

# Create chatbot instance
chatbot = Chatbot()