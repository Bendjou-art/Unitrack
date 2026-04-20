import sqlite3
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "database.db")

conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS etudiant (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT,
    prenom TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS note (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_etudiant INTEGER,
    note REAL
)""")

# Admin par défaut (ne recrée pas si existe déjà)
c.execute("INSERT OR IGNORE INTO admin (username, password) VALUES ('admin', '1234')")

conn.commit()
conn.close()
print("Base de données créée avec succès !")