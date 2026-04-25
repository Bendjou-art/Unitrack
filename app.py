import os
import sqlite3
from flask import Flask, render_template, request, redirect, g, flash

# ================= CONFIGURATION DES CHEMINS =================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
DATABASE = os.path.join(BASE_DIR, "database.db")

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.config['SECRET_KEY'] = 'ma_cle_unitaire_track_2026'

# ================= GESTION DE LA BASE DE DONNÉES =================

def get_db():
    """Connexion avec gestion des clés étrangères."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# ================= ROUTES ÉTUDIANTS =================

@app.route('/')
def home():
    return redirect('/students')

@app.route('/students')
def students():
    db = get_db()
    data = db.execute("SELECT * FROM etudiant").fetchall()
    return render_template("students.html", students=data)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        db = get_db()
        try:
            db.execute(
                "INSERT INTO etudiant (nom, prenom, matricule) VALUES (?, ?, ?)",
                (request.form['nom'], request.form['prenom'], request.form['matricule'])
            )
            db.commit()
            return redirect('/students')
        except sqlite3.Error as e:
            return f"Erreur lors de la création de l'étudiant : {e}", 500
    return render_template("add_student.html")

# ================= GESTION DES NOTES =================

@app.route('/add_notes/<int:id>', methods=['GET', 'POST'])
def add_notes(id):
    if request.method == 'POST':
        db = get_db()
        semestre = request.form.get('semestre')
        try:
            for i in range(1, 7):
                matiere = request.form.get(f"matiere{i}")
                note_val = request.form.get(f"note{i}")
                if matiere and note_val:
                    db.execute(
                        "INSERT INTO note (etudiant_id, matiere, note, semestre) VALUES (?, ?, ?, ?)",
                        (id, matiere, float(note_val), int(semestre))
                    )
            db.commit()
            return redirect('/students')
        except (sqlite3.Error, ValueError) as e:
            db.rollback()
            return f"Erreur de saisie des notes : {e}", 500
    return render_template("add_notes.html", id=id)

# ================= EMPLOI DU TEMPS & PLANNING =================

@app.route('/add_schedule/<int:id>', methods=['GET', 'POST'])
def add_schedule(id):
    if request.method == 'POST':
        db = get_db()
        try:
            # Gestion du format HH:MM ou entier
            debut_raw = request.form['debut']
            fin_raw = request.form['fin']
            h_debut = int(debut_raw.split(':')[0]) if ':' in debut_raw else int(debut_raw)
            h_fin = int(fin_raw.split(':')[0]) if ':' in fin_raw else int(fin_raw)

            db.execute(
                "INSERT INTO emploi (etudiant_id, jour, heure_debut, heure_fin, matiere) VALUES (?, ?, ?, ?, ?)",
                (id, request.form['jour'], h_debut, h_fin, request.form['matiere'])
            )
            db.commit()
            return redirect(f'/planning/{id}')
        except (sqlite3.Error, ValueError) as e:
            return f"Format d'heure invalide : {e}", 400
    return render_template("add_schedule.html", id=id)

# --- NOUVELLE ROUTE : AJOUT DE TÂCHES (TRANSACTIONS) ---
@app.route('/add_transaction/<int:id>', methods=['GET', 'POST'])
def add_transaction(id):
    if request.method == 'POST':
        db = get_db()
        try:
            # Notez l'utilisation des guillemets pour "transaction" (mot réservé)
            db.execute(
                'INSERT INTO "transaction" (etudiant_id, description, duree) VALUES (?, ?, ?)',
                (id, request.form['description'], int(request.form['duree']))
            )
            db.commit()
            return redirect(f'/planning/{id}')
        except (sqlite3.Error, ValueError) as e:
            return f"Erreur lors de l'ajout de la tâche : {e}", 500
    return render_template("add_transaction.html", id=id)

@app.route('/planning/<int:id>')
def planning(id):
    db = get_db()
    # On récupère les cours triés par heure
    cours = db.execute("SELECT * FROM emploi WHERE etudiant_id=? ORDER BY heure_debut", (id,)).fetchall()
    # On récupère les tâches (transactions)
    tasks = db.execute('SELECT * FROM "transaction" WHERE etudiant_id=?', (id,)).fetchall()

    libres = []
    current_time = 8 # Début journée

    # Détection des trous dans l'emploi du temps
    for c in cours:
        h_debut = int(c['heure_debut'])
        h_fin = int(c['heure_fin'])
        if h_debut > current_time:
            libres.append([current_time, h_debut])
        current_time = max(current_time, h_fin)

    if current_time < 18: # Fin journée
        libres.append([current_time, 18])

    res_planning = []
    # Remplissage intelligent des trous
    for t in tasks:
        duree = int(t['duree'])
        for l in libres:
            if (l[1] - l[0]) >= duree:
                res_planning.append({
                    "task": t['description'],
                    "start": l[0],
                    "end": l[0] + duree
                })
                l[0] += duree # On décale le début du créneau libre
                break

    return render_template("planning.html", planning=res_planning, id=id)

# ================= STATISTIQUES =================

@app.route('/stats/<int:id>')
def stats(id):
    db = get_db()
    s1 = [float(n['note']) for n in db.execute("SELECT note FROM note WHERE etudiant_id=? AND semestre=1", (id,)).fetchall()]
    s2 = [float(n['note']) for n in db.execute("SELECT note FROM note WHERE etudiant_id=? AND semestre=2", (id,)).fetchall()]

    m1 = sum(s1) / len(s1) if s1 else 0
    m2 = sum(s2) / len(s2) if s2 else 0
    
    if s1 and s2:
        mg = (m1 + m2) / 2
    else:
        mg = m1 if s1 else m2

    return render_template("stats.html", m1=round(m1, 2), m2=round(m2, 2), mg=round(mg, 2), s1=s1, s2=s2, id=id)

# ================= LANCEMENT =================

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)