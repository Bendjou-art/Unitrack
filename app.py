import os
import sqlite3
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "secret123"

def get_db():
    # Chemin absolu qui marche à la fois en local et sur PythonAnywhere
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "database.db")
    return sqlite3.connect(db_path)

# ====================== ROUTES ======================

@app.route('/')
def home():
    return '''
    <h1>Menu Principal</h1>
    <p><a href="/login">→ Connexion Admin</a></p>
    <p><a href="/dashboard">→ Dashboard (après connexion)</a></p>
    <p><a href="/stats">→ Statistiques (après connexion)</a></p>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        db = get_db()
        admin = db.execute(
            "SELECT * FROM admin WHERE username=? AND password=?",
            (username, password)
        ).fetchone()

        if admin:
            session['user'] = username
            return redirect('/dashboard')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM etudiant").fetchone()[0]

    return render_template('dashboard.html', total=total)

@app.route('/stats')
def stats():
    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    moyenne = db.execute("SELECT AVG(note) FROM note").fetchone()[0] or 0
    notes = db.execute("SELECT note FROM note").fetchall()
    notes_list = [n[0] for n in notes]

    return render_template('stats.html', moyenne=moyenne, notes=notes_list)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# Pour lancer en local seulement
if __name__ == '__main__':
    app.run(debug=True)