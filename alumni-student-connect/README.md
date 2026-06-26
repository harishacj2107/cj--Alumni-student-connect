# Alumni-Student Connect Portal

## Project Description
A web-based platform to connect college alumni with current students for mentorship and career guidance. Alumni can register, update their profiles, and chat with students. Students can search alumni by name, company, course, or batch and initiate chats.

## Features
- Alumni Registration and Profile Management
- Student Registration with College ID
- Search Alumni by Filters
- One-to-One Messaging (AJAX-based)
- Admin Panel for Verification and Monitoring
- Secure Authentication

## Technology Stack
- **Frontend**: HTML, CSS, Bootstrap, JavaScript
- **Backend**: Python Flask
- **Database**: SQLite
- **Messaging**: AJAX polling (every 5 seconds)

## Setup Instructions
1. **Prerequisites**:
   - Python 3.x
   - Flask (`pip install flask`)
   - Werkzeug (`pip install werkzeug`)
   - SQLite (included with Python)

2. **Installation**:
   - Clone or download the project.
   - Navigate to the project directory: `cd alumni-student-connect`
   - Install dependencies: `pip install -r requirements.txt` (create one with `flask` and `werkzeug`)

3. **Run the Application**:
   - Run `python app.py`
   - Open `http://localhost:5000` in your browser.

4. **Default Admin Credentials**:
   - Username: `admin`
   - Password: `admin123`

## Database Schema
The database is initialized automatically in `alumni.db`. See `schema.sql` for the structure.

## Usage
1. **Admin**: Log in to approve/reject alumni registrations and view student records.
2. **Alumni**: Register, wait for admin approval, update profile, and respond to student messages.
3. **Student**: Register with college ID, search alumni, and initiate chats.

## Future Scope
- Video calling integration
- Mentorship session scheduler
- Alumni event notifications
- Career opportunity sharing
- Mobile app version

## Notes
- The messaging system uses AJAX polling for simplicity. For production, consider WebSocket for real-time messaging.
- Passwords are hashed using Werkzeug's `generate_password_hash`.
- SQLite is used for simplicity; replace with MySQL/PostgreSQL for production.