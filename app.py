from flask import Flask, render_template, request, redirect, g
import sqlite3
import os

app = Flask(__name__)
DATABASE = "database.db"

# ================= GESTION DE LA BASE DE DONNÉES =================
def get_db():
    """Ouvre une connexion à la BDD si elle n'existe pas déjà pour cette requête."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    """Ferme la BDD automatiquement à la fin de chaque requête Flask."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Initialisation au démarrage
if not os.path.exists(DATABASE):
    try:
        import init_db
    except ImportError:
        print("Attention : le fichier init_db.py est introuvable.")

# ================= ROUTES =================

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
            db.execute("INSERT INTO etudiant (nom, prenom, matricule) VALUES (?, ?, ?)",
                       (request.form['nom'], request.form['prenom'], request.form['matricule']))
            db.commit()
        except sqlite3.Error as e:
            print(f"Erreur base de données : {e}")
            # Tu pourrais ici retourner un message d'erreur à l'utilisateur
        return redirect('/students')
    
    return render_template("add_student.html")

@app.route('/add_notes/<int:id>', methods=['GET', 'POST'])
def add_notes(id):
    if request.method == 'POST':
        db = get_db()
        semestre = request.form['semestre']
        try:
            # On boucle sur les 6 matières
            for i in range(1, 7):
                db.execute("INSERT INTO note (etudiant_id, matiere, note, semestre) VALUES (?, ?, ?, ?)",
                           (id, request.form[f"matiere{i}"], request.form[f"note{i}"], semestre))
            db.commit()
        except sqlite3.Error as e:
             print(f"Erreur base de données : {e}")
        return redirect('/students')
        
    return render_template("add_notes.html", id=id)

@app.route('/add_schedule/<int:id>', methods=['GET', 'POST'])
def add_schedule(id):
    if request.method == 'POST':
        db = get_db()
        try:
            # Toujours préciser les colonnes pour éviter les crashs si le schéma change
            db.execute("INSERT INTO emploi (etudiant_id, jour, heure_debut, heure_fin, matiere) VALUES (?, ?, ?, ?, ?)",
                       (id, request.form['jour'], request.form['debut'], request.form['fin'], request.form['matiere']))
            db.commit()
        except sqlite3.Error as e:
             print(f"Erreur base de données : {e}")
        # CORRECTION : Il manquait le redirect ici dans ton code d'origine !
        return redirect('/students') 
        
    return render_template("add_schedule.html", id=id)

@app.route('/add_transaction/<int:id>', methods=['GET', 'POST'])
def add_transaction(id):
    if request.method == 'POST':
        db = get_db()
        try:
            db.execute("INSERT INTO transaction (etudiant_id, description, duree) VALUES (?, ?, ?)",
                       (id, request.form['description'], request.form['duree']))
            db.commit()
        except sqlite3.Error as e:
             print(f"Erreur base de données : {e}")
        return redirect('/students')
        
    return render_template("add_transaction.html", id=id)

@app.route('/planning/<int:id>')
def planning(id):
    db = get_db()
    cours = db.execute("SELECT * FROM emploi WHERE etudiant_id=? ORDER BY heure_debut", (id,)).fetchall()
    tasks = db.execute("SELECT * FROM transaction WHERE etudiant_id=?", (id,)).fetchall()

    libres = []
    current = 8 # Début de journée à 8h

    # Logique de calcul des temps libres
    for c in cours:
        heure_debut = int(c['heure_debut'])
        heure_fin = int(c['heure_fin'])
        
        if heure_debut > current:
            libres.append([current, heure_debut])
        current = max(current, heure_fin) # Utilisation de max() pour éviter les chevauchements bizarres

    if current < 18: # Fin de journée à 18h
        libres.append([current, 18])

    planning = []

    # Attribution des tâches dans les temps libres
    for t in tasks:
        duree = int(t['duree'])
        for l in libres:
            # l[0] = début temps libre, l[1] = fin temps libre
            if (l[1] - l[0]) >= duree:
                planning.append({
                    "task": t['description'],
                    "start": l[0],
                    "end": l[0] + duree
                })
                l[0] += duree # On réduit le temps libre disponible
                break # On passe à la tâche suivante

    return render_template("planning.html", planning=planning)

@app.route('/stats/<int:id>')
def stats(id):
    db = get_db()
    s1_rows = db.execute("SELECT note FROM note WHERE etudiant_id=? AND semestre=1", (id,)).fetchall()
    s2_rows = db.execute("SELECT note FROM note WHERE etudiant_id=? AND semestre=2", (id,)).fetchall()

    s1 = [n['note'] for n in s1_rows]
    s2 = [n['note'] for n in s2_rows]

    # Utilisation conditionnelle plus sûre
    m1 = sum(s1) / len(s1) if s1 else 0
    m2 = sum(s2) / len(s2) if s2 else 0
    mg = (m1 + m2) / 2 if (s1 and s2) else (m1 or m2) # Permet de calculer une moyenne générale correcte s'il manque un semestre

    return render_template("stats.html", m1=m1, m2=m2, mg=mg, s1=s1, s2=s2)

if __name__ == '__main__':
    app.run(debug=True)