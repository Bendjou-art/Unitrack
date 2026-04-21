from flask import Flask, render_template, request, redirect, session
import sqlite3
import bcrypt

app = Flask(__name__)
app.secret_key = "super_secret_key"

def get_db():
    return sqlite3.connect("database.db")

# LOGIN
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        admin = db.execute(
            "SELECT * FROM admin WHERE username=?",
            (username,)
        ).fetchone()

        if admin and bcrypt.checkpw(password.encode('utf-8'), admin[2]):
            session['user'] = username
            return redirect('/dashboard')

    return render_template('login.html')

# DASHBOARD
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM etudiant").fetchone()[0]

    return render_template('dashboard.html', total=total)

# AJOUT ETUDIANT
@app.route('/add_student', methods=['GET','POST'])
def add_student():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']

        db = get_db()
        db.execute("INSERT INTO etudiant (nom, prenom) VALUES (?, ?)", (nom, prenom))
        db.commit()

        return redirect('/dashboard')

    return render_template('add_student.html')

# STATISTIQUES
@app.route('/stats')
def stats():
    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    moyenne = db.execute("SELECT AVG(note) FROM note").fetchone()[0]
    notes = db.execute("SELECT note FROM note").fetchall()

    notes_list = [n[0] for n in notes]

    return render_template('stats.html', moyenne=moyenne, notes=notes_list)

# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)