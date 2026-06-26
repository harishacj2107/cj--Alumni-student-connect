from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime
import re
from uuid import uuid4
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

def is_valid_email(email):
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def is_valid_password(password):
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True

def is_valid_student_id(student_id):
    # Pattern: 1BI<year><branch><roll>, where year is 2 digits, branch is 2 chars, roll is 3 digits
    pattern = r'^1BI(\d{2})(MC|MBA)(\d{3})$'
    if not re.match(pattern, student_id):
        return False
    year = int(re.match(pattern, student_id).group(1))
    # Validate year (e.g., 2000–2025 for now)
    if year < 2000 or year > 2025:
        return False
    return True

def init_db():
    with sqlite3.connect('alumni.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS admin (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS alumni (
            alumni_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            job TEXT,
            company TEXT,
            course TEXT,
            batch INTEGER,
            status TEXT DEFAULT 'pending'
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            branch TEXT,
            college_id TEXT UNIQUE
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            receiver_id INTEGER,
            content TEXT,
            timestamp TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS password_resets (
            token TEXT PRIMARY KEY,
            email TEXT,
            expiry TIMESTAMP,
            FOREIGN KEY (email) REFERENCES alumni(email) ON DELETE CASCADE,
            FOREIGN KEY (email) REFERENCES students(email) ON DELETE CASCADE
        )''')
        c.execute("INSERT OR IGNORE INTO admin (username, password) VALUES (?, ?)",
                 ('admin', generate_password_hash('admin123')))
        conn.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect('alumni.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM admin WHERE username = ?", (username,))
            admin = c.fetchone()
            if admin and check_password_hash(admin[2], password):
                session['admin_id'] = admin[0]
                return redirect(url_for('admin_dashboard'))
        return render_template('admin_login.html', error="Invalid credentials")
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    with sqlite3.connect('alumni.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM alumni WHERE status = 'pending'")
        pending_alumni = c.fetchall()
        c.execute("SELECT * FROM alumni WHERE status = 'approved'")
        approved_alumni = c.fetchall()
        c.execute("SELECT * FROM students")
        students = c.fetchall()
    return render_template('admin_dashboard.html', pending_alumni=pending_alumni, approved_alumni=approved_alumni, students=students)

@app.route('/admin/approve/<int:alumni_id>')
def admin_approve(alumni_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    with sqlite3.connect('alumni.db') as conn:
        c = conn.cursor()
        c.execute("UPDATE alumni SET status = 'approved' WHERE alumni_id = ?", (alumni_id,))
        conn.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject/<int:alumni_id>')
def admin_reject(alumni_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    with sqlite3.connect('alumni.db') as conn:
        c = conn.cursor()
        c.execute("DELETE FROM alumni WHERE alumni_id = ?", (alumni_id,))
        conn.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_alumni/<int:alumni_id>')
def admin_delete_alumni(alumni_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    with sqlite3.connect('alumni.db') as conn:
        c = conn.cursor()
        c.execute("DELETE FROM alumni WHERE alumni_id = ?", (alumni_id,))
        conn.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_student/<int:student_id>')
def admin_delete_student(student_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    with sqlite3.connect('alumni.db') as conn:
        c = conn.cursor()
        c.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
        conn.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/alumni/register', methods=['GET', 'POST'])
def alumni_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        job = request.form['job']
        company = request.form['company']
        course = request.form['course']
        batch = request.form['batch']
        if not is_valid_email(email):
            return render_template('alumni_register.html', error="Please enter a valid email address")
        if not is_valid_password(password):
            return render_template('alumni_register.html', error="Password must be at least 8 characters long and include one uppercase letter, one lowercase letter, one digit, and one special character (e.g., !@#$%^&*())")
        password_hash = generate_password_hash(password)
        with sqlite3.connect('alumni.db') as conn:
            c = conn.cursor()
            try:
                c.execute("INSERT INTO alumni (name, email, password, job, company, course, batch) VALUES (?, ?, ?, ?, ?, ?, ?)",
                         (name, email, password_hash, job, company, course, batch))
                conn.commit()
                return redirect(url_for('alumni_login'))
            except sqlite3.IntegrityError:
                return render_template('alumni_register.html', error="Email already exists")
    return render_template('alumni_register.html')

@app.route('/alumni/login', methods=['GET', 'POST'])
def alumni_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        with sqlite3.connect('alumni.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM alumni WHERE email = ? AND status = 'approved'", (email,))
            alumni = c.fetchone()
            if alumni and check_password_hash(alumni[3], password):
                session['alumni_id'] = alumni[0]
                session['alumni_name'] = alumni[1]  # Store the alumni's name in session
                return redirect(url_for('alumni_dashboard'))
            elif alumni and not check_password_hash(alumni[3], password):
                return render_template('alumni_login.html', error="Invalid password")
        return render_template('alumni_login.html', error="Invalid credentials or account not approved")
    return render_template('alumni_login.html')

@app.route('/alumni/dashboard')
def alumni_dashboard():
    if 'alumni_id' not in session:
        return redirect(url_for('alumni_login'))
    with sqlite3.connect('alumni.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM alumni WHERE alumni_id = ?", (session['alumni_id'],))
        alumni = c.fetchone()
        c.execute("SELECT * FROM messages WHERE receiver_id = ?", (session['alumni_id'],))
        messages = c.fetchall()
    return render_template('alumni_dashboard.html', alumni=alumni, messages=messages, alumni_name=session.get('alumni_name'))

@app.route('/alumni/update', methods=['GET', 'POST'])
def alumni_update():
    if 'alumni_id' not in session:
        return redirect(url_for('alumni_login'))
    if request.method == 'POST':
        job = request.form['job']
        company = request.form['company']
        course = request.form['course']
        batch = request.form['batch']
        with sqlite3.connect('alumni.db') as conn:
            c = conn.cursor()
            c.execute("UPDATE alumni SET job = ?, company = ?, course = ?, batch = ? WHERE alumni_id = ?",
                     (job, company, course, batch, session['alumni_id']))
            conn.commit()
        return redirect(url_for('alumni_dashboard'))
    with sqlite3.connect('alumni.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM alumni WHERE alumni_id = ?", (session['alumni_id'],))
        alumni = c.fetchone()
    return render_template('alumni_update.html', alumni=alumni)

@app.route('/student/register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        branch = request.form['branch']
        college_id = request.form['college_id']
        if not is_valid_email(email):
            return render_template('student_register.html', error="Please enter a valid email address")
        if not is_valid_password(password):
            return render_template('student_register.html', error="Password must be at least 8 characters long and include one uppercase letter, one lowercase letter, one digit, and one special character (e.g., !@#$%^&*())")
        if not is_valid_student_id(college_id):
            return render_template('student_register.html', error="Invalid student ID format. Use format: 1BI<year><branch><roll> (e.g., 1BI24MC001 for MCA or 1BI24MBA001 for MBA)")
        password_hash = generate_password_hash(password)
        with sqlite3.connect('alumni.db') as conn:
            c = conn.cursor()
            try:
                c.execute("INSERT INTO students (name, email, password, branch, college_id) VALUES (?, ?, ?, ?, ?)",
                         (name, email, password_hash, branch, college_id))
                conn.commit()
                return redirect(url_for('student_login'))
            except sqlite3.IntegrityError:
                return render_template('student_register.html', error="Email or College ID already exists")
    return render_template('student_register.html')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        with sqlite3.connect('alumni.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM students WHERE email = ?", (email,))
            student = c.fetchone()
            if student and check_password_hash(student[3], password):
                session['student_id'] = student[0]
                return redirect(url_for('student_dashboard'))
            elif student and not check_password_hash(student[3], password):
                return render_template('student_login.html', error="Invalid password")
        return render_template('student_login.html', error="Invalid credentials")
    return render_template('student_login.html')

@app.route('/student/dashboard')
def student_dashboard():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    with sqlite3.connect('alumni.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM alumni WHERE status = 'approved'")
        alumni = c.fetchall()
    return render_template('student_dashboard.html', alumni=alumni)

@app.route('/student/search', methods=['GET'])
def student_search():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    query = request.args.get('query', '')
    with sqlite3.connect('alumni.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM alumni WHERE status = 'approved' AND (name LIKE ? OR company LIKE ? OR course LIKE ? OR batch LIKE ?)",
                 (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
        alumni = c.fetchall()
    return render_template('student_dashboard.html', alumni=alumni, query=query)

@app.route('/chat/<int:receiver_id>', methods=['GET', 'POST'])
def chat(receiver_id):
    if 'student_id' not in session and 'alumni_id' not in session:
        return redirect(url_for('index'))
    sender_id = session.get('student_id') or session.get('alumni_id')
    if request.method == 'POST':
        content = request.form['content']
        with sqlite3.connect('alumni.db') as conn:
            c = conn.cursor()
            c.execute("INSERT INTO messages (sender_id, receiver_id, content, timestamp) VALUES (?, ?, ?, ?)",
                     (sender_id, receiver_id, content, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
    with sqlite3.connect('alumni.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM messages WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)",
                 (sender_id, receiver_id, receiver_id, sender_id))
        messages = c.fetchall()
        c.execute("SELECT * FROM alumni WHERE alumni_id = ? AND status = 'approved'", (receiver_id,))
        receiver = c.fetchone()
        if not receiver:
            c.execute("SELECT * FROM students WHERE student_id = ?", (receiver_id,))
            receiver = c.fetchone()
    return render_template('chat.html', messages=messages, receiver=receiver, receiver_id=receiver_id)

@app.route('/chat/messages/<int:receiver_id>')
def get_messages(receiver_id):
    sender_id = session.get('student_id') or session.get('alumni_id')
    with sqlite3.connect('alumni.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM messages WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)",
                 (sender_id, receiver_id, receiver_id, sender_id))
        messages = c.fetchall()
    return jsonify(messages)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if not email:
            return render_template('forgot_password.html', error="Please enter an email address")
        if not is_valid_email(email):
            return render_template('forgot_password.html', error="Invalid email format")
        
        token = str(uuid4())
        expiry = time.time() + 3600  # Token valid for 1 hour
        print(f"Generated reset token for {email}: http://localhost:5000/reset_password/{token}")
        
        try:
            with sqlite3.connect('alumni.db') as conn:
                c = conn.cursor()
                c.execute("SELECT email FROM alumni WHERE email = ?", (email,))
                if c.fetchone():
                    c.execute("INSERT INTO password_resets (token, email, expiry) VALUES (?, ?, ?)",
                             (token, email, expiry))
                    conn.commit()
                else:
                    c.execute("SELECT email FROM students WHERE email = ?", (email,))
                    if c.fetchone():
                        c.execute("INSERT INTO password_resets (token, email, expiry) VALUES (?, ?, ?)",
                                 (token, email, expiry))
                        conn.commit()
                    else:
                        return render_template('forgot_password.html', error="Email not found")
        except sqlite3.Error as e:
            print(f"Database error: {str(e)}")
            return render_template('forgot_password.html', error="An error occurred. Check the terminal")
        
        return render_template('forgot_password.html', message="A password reset link has been generated. Check the terminal for the token.")
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    with sqlite3.connect('alumni.db') as conn:
        c = conn.cursor()
        c.execute("SELECT email, expiry FROM password_resets WHERE token = ?", (token,))
        reset = c.fetchone()
        if not reset or time.time() > reset[1]:
            return "Invalid or expired token"
        if request.method == 'POST':
            new_password = request.form['password']
            if not is_valid_password(new_password):
                return render_template('reset_password.html', token=token, error="Password must be at least 8 characters long and include one uppercase letter, one lowercase letter, one digit, and one special character (e.g., !@#$%^&*())")
            new_password_hash = generate_password_hash(new_password)
            email = reset[0]
            c.execute("SELECT email FROM alumni WHERE email = ?", (email,))
            if c.fetchone():
                c.execute("UPDATE alumni SET password = ? WHERE email = ?", (new_password_hash, email))
            else:
                c.execute("UPDATE students SET password = ? WHERE email = ?", (new_password_hash, email))
            c.execute("DELETE FROM password_resets WHERE token = ?", (token,))
            conn.commit()
            return redirect(url_for('index'))
        return render_template('reset_password.html', token=token)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)