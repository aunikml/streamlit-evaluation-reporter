# db_utils.py

import sqlite3
import hashlib

def hash_password(password):
    """Hashes the password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """Initializes the database and creates the users table if it doesn't exist."""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # Create table with username, hashed_password, and role
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    # Check if the default admin user exists
    c.execute("SELECT * FROM users WHERE username = ?", ('admin',))
    if c.fetchone() is None:
        # If not, create a default admin user with password 'admin'
        hashed_admin_password = hash_password('admin')
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  ('admin', hashed_admin_password, 'admin'))
    conn.commit()
    conn.close()

def add_user(username, password, role):
    """Adds a new user to the database. Returns True on success, False otherwise."""
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        hashed_password = hash_password(password)
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  (username, hashed_password, role))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        # This error occurs if the username already exists
        return False

def verify_user(username, password):
    """Verifies user credentials. Returns user's role if valid, None otherwise."""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT password, role FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    if result:
        stored_password_hash, role = result
        entered_password_hash = hash_password(password)
        if stored_password_hash == entered_password_hash:
            return role  # Return the user's role on successful login
    return None

def get_all_users():
    """Retrieves all users and their roles from the database."""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT username, role FROM users")
    users = c.fetchall()
    conn.close()
    return users