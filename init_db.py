import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

# On active le support des clés étrangères
c.execute("PRAGMA foreign_keys = ON")

# --- TABLE ETUDIANT ---
c.execute("""
CREATE TABLE IF NOT EXISTS etudiant (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    matricule TEXT UNIQUE NOT NULL
)
""")

# --- TABLE NOTE ---
c.execute("""
CREATE TABLE IF NOT EXISTS note (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    etudiant_id INTEGER,
    matiere TEXT NOT NULL,
    note REAL CHECK(note >= 0 AND note <= 20),
    semestre INTEGER,
    FOREIGN KEY (etudiant_id) REFERENCES etudiant (id) ON DELETE CASCADE
)
""")

# --- TABLE EMPLOI ---
c.execute("""
CREATE TABLE IF NOT EXISTS emploi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    etudiant_id INTEGER,
    jour TEXT NOT NULL,
    heure_debut INTEGER NOT NULL,
    heure_fin INTEGER NOT NULL,
    matiere TEXT NOT NULL,
    FOREIGN KEY (etudiant_id) REFERENCES etudiant (id) ON DELETE CASCADE
)
""")

# --- TABLE TRANSACTION (CORRIGÉ AVEC DES GUILLEMETS) ---
# En utilisant "transaction", SQLite comprend que c'est le NOM de la table
c.execute("""
CREATE TABLE IF NOT EXISTS "transaction" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    etudiant_id INTEGER,
    description TEXT NOT NULL,
    duree INTEGER NOT NULL,
    FOREIGN KEY (etudiant_id) REFERENCES etudiant (id) ON DELETE CASCADE
)
""")

conn.commit()
conn.close()
print("Base de données initialisée avec succès !")