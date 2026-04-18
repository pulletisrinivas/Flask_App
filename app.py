from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- DATABASE ----------------
def get_db():
    db_path = os.path.join(os.getcwd(), "database.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- CREATE TABLES (AUTO) ----------------
def init_db():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        username TEXT,
        email TEXT,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        user_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    db.commit()

init_db()

# ---------------- HOME ----------------
@app.route('/')
def home():
    return redirect('/login')

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()

        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        mail = cursor.fetchone()

        if user:
            flash("Username already exists", "danger")
        elif mail:
            flash("Email already registered", "danger")
        else:
            cursor.execute(
                "INSERT INTO users(name, username, email, password) VALUES(?,?,?,?)",
                (name, username, email, password)
            )
            db.commit()

            flash("Registration Successful", "success")
            return redirect('/login')

    return render_template('register.html')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['name'] = user['name'] or user['username']

            flash(f"Welcome {session['name']}!", "success")
            return redirect('/welcome')
        else:
            flash("Invalid email or password", "danger")

    return render_template('login.html')

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect('/login')

# ---------------- FORGOT PASSWORD ----------------
@app.route('/forgot', methods=['GET','POST'])
def forgot():
    if request.method == 'POST':
        email = request.form['email']
        new_password = generate_password_hash(request.form['password'])

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "UPDATE users SET password=? WHERE email=?",
            (new_password, email)
        )
        db.commit()

        flash("Password updated successfully", "success")
        return redirect('/login')

    return render_template('forgot.html')

# ---------------- WELCOME ----------------
@app.route('/welcome')
def welcome():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('welcome.html')

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM notes WHERE user_id=? ORDER BY created_at DESC",
        (session['user_id'],)
    )
    notes = cursor.fetchall()

    return render_template('dashboard.html', notes=notes)

# ---------------- ADD NOTE ----------------
@app.route('/addnote', methods=['GET','POST'])
def addnote():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "INSERT INTO notes(title, content, user_id) VALUES(?,?,?)",
            (title, content, session['user_id'])
        )
        db.commit()

        flash("Note Added Successfully", "success")
        return redirect('/dashboard')

    return render_template('add_note.html')

# ---------------- VIEW NOTE ----------------
@app.route('/view/<int:id>')
def view(id):
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM notes WHERE id=?", (id,))
    note = cursor.fetchone()

    if not note or note['user_id'] != session['user_id']:
        return "Unauthorized Access"

    return render_template('view_note.html', note=note)

# ---------------- EDIT NOTE ----------------
@app.route('/edit/<int:id>', methods=['GET','POST'])
def edit(id):
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM notes WHERE id=?", (id,))
    note = cursor.fetchone()

    if not note or note['user_id'] != session['user_id']:
        return "Unauthorized Access"

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        cursor.execute(
            "UPDATE notes SET title=?, content=? WHERE id=?",
            (title, content, id)
        )
        db.commit()

        flash("Note Updated", "info")
        return redirect('/dashboard')

    return render_template('edit_note.html', note=note)

# ---------------- DELETE NOTE ----------------
@app.route('/delete/<int:id>')
def delete(id):
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM notes WHERE id=?", (id,))
    note = cursor.fetchone()

    if not note or note['user_id'] != session['user_id']:
        return "Unauthorized Access"

    cursor.execute("DELETE FROM notes WHERE id=?", (id,))
    db.commit()

    flash("Note Deleted", "warning")
    return redirect('/dashboard')

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)