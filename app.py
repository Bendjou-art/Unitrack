import os
import sqlite3
from flask import Flask, render_template, request, redirect, g, flash

# ================= CONFIGURATION DES CHEMINS =================
# On s'assure que Flask trouve toujours les fichiers, peu importe d'où on lance le script
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
DATABASE = os.path.join(BASE_DIR, "database.db")

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.config['SECRET_KEY'] = 'une_cle_tres_secrete_123'

# ================= GESTION DE LA BASE DE DONNÉES =================

def get_db():
    """Connexion sécurisée à la base de données SQLite."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        # Force SQLite à vérifier que l'étudiant existe avant d'ajouter une note
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(exception):
    """Ferme la connexion proprement après chaque page chargée."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Vérification du fichier de base de données au démarrage
if not os.path.exists(DATABASE):
    print("--- INFO : Base de données absente, création en cours... ---")
    try:
        import init_db
    except ImportError:
        print("--- ERREUR : Le fichier init_db.py est manquant pour créer la base ! ---")

# ================= ROUTES PRINCIPALES =================

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
            return f"Erreur SQL lors de l'ajout de l'étudiant : {e}", 500
    
    return render_template("add_student.html")

# ================= GESTION DES NOTES =================

@app.route('/add_notes/<int:id>', methods=['GET', 'POST'])
def add_notes(id):
    if request.method == 'POST':
        db = get_db()
        semestre = request.form.get('semestre')
        try:
            # On vérifie chaque champ de matière (1 à 6)
            for i in range(1, 7):
                matiere = request.form.get(f"matiere{i}")
                note_val = request.form.get(f"note{i}")
                
                if matiere and note_val: # On n'enregistre que si les deux sont remplis
                    db.execute(
                        "INSERT INTO note (etudiant_id, matiere, note, semestre) VALUES (?, ?, ?, ?)",
                        (id, matiere, float(note_val), int(semestre))
                    )
            db.commit()
            return redirect('/students')
        except (sqlite3.Error, ValueError) as e:
            db.rollback() # Annule tout si une seule insertion échoue
            return f"Erreur lors de l'enregistrement des notes : {e}", 500
            
    return render_template("add_notes.html", id=id)

# ================= PLANNING ET EMPLOI DU TEMPS =================

@app.route('/add_schedule/<int:id>', methods=['GET', 'POST'])
def add_schedule(id):
    if request.method == 'POST':
        db = get_db()
        try:
            db.execute(
                "INSERT INTO emploi (etudiant_id, jour, heure_debut, heure_fin, matiere) VALUES (?, ?, ?, ?, ?)",
                (id, request.form['jour'], int(request.form['debut']), int(request.form['fin']), request.form['matiere'])
            )
            db.commit()
            return redirect(f'/planning/{id}')
        except sqlite3.Error as e:
            return f"Erreur lors de l'ajout à l'emploi du temps : {e}", 500
            
    return render_template("add_schedule.html", id=id)

@app.route('/planning/<int:id>')
def planning(id):
    db = get_db()
    # On récupère les cours triés par heure pour le calcul des trous (temps libres)
    cours = db.execute("SELECT * FROM emploi WHERE etudiant_id=? ORDER BY heure_debut", (id,)).fetchall()
    tasks = db.execute("SELECT * FROM transaction WHERE etudiant_id=?", (id,)).fetchall()

    libres = []
    current_time = 8  # On commence la journée à 8h

    for c in cours:
        h_debut = int(c['heure_debut'])
        h_fin = int(c['heure_fin'])
        # S'il y a un espace entre l'heure actuelle et le prochain cours
        if h_debut > current_time:
            libres.append([current_time, h_debut])
        # On avance l'heure à la fin du cours actuel
        current_time = max(current_time, h_fin)

    # Si la journée n'est pas finie à 18h, on ajoute le temps restant
    if current_time < 18:
        libres.append([current_time, 18])

    res_planning = []
    # On essaie de placer chaque tâche dans un créneau libre
    for t in tasks:
        duree = int(t['duree'])
        for l in libres:
            if (l[1] - l[0]) >= duree:
                res_planning.append({
                    "task": t['description'],
                    "start": l[0],
                    "end": l[0] + duree
                })
                l[0] += duree # On réduit l'espace libre consommé
                break

    return render_template("planning.html", planning=res_planning, id=id)

# ================= STATISTIQUES =================

@app.route('/stats/<int:id>')
def stats(id):
    db = get_db()
    # Récupération des notes par semestre
    s1 = [float(n['note']) for n in db.execute("SELECT note FROM note WHERE etudiant_id=? AND semestre=1", (id,)).fetchall()]
    s2 = [float(n['note']) for n in db.execute("SELECT note FROM note WHERE etudiant_id=? AND semestre=2", (id,)).fetchall()]

    m1 = sum(s1) / len(s1) if s1 else 0
    m2 = sum(s2) / len(s2) if s2 else 0
    
    # Moyenne générale (mg)
    if s1 and s2:
        mg = (m1 + m2) / 2
    else:
        mg = m1 if s1 else m2

    return render_template("stats.html", 
                           m1=round(m1, 2), 
                           m2=round(m2, 2), 
                           mg=round(mg, 2), 
                           s1=s1, s2=s2, id=id)

# ================= LANCEMENT =================

if __name__ == '__main__':
    # host='0.0.0.0' permet d'accéder au site depuis d'autres appareils sur le même réseau
    app.run(host='127.0.0.1', port=5000, debug=True)