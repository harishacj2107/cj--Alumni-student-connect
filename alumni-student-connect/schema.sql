CREATE TABLE admin (
    admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
);

CREATE TABLE alumni (
    alumni_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    job TEXT,
    company TEXT,
    course TEXT,
    batch INTEGER,
    status TEXT DEFAULT 'pending'
);

CREATE TABLE students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    branch TEXT,
    college_id TEXT UNIQUE
);

CREATE TABLE messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER,
    receiver_id INTEGER,
    content TEXT,
    timestamp TEXT
);

INSERT INTO admin (username, password) VALUES ('admin', '$2b$12$...'); -- Replace with hashed password