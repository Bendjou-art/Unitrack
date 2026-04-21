import sqlite3
import bcrypt

conn = sqlite3.connect("database.db")
c = conn.cursor()

print("🔄 Initialisation de la base de données...")

# TABLE ADMIN
c.execute('''CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)''')

# TABLE ETUDIANT
c.execute('''CREATE TABLE IF NOT EXISTS etudiant (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL
)''')

# TABLE NOTE
c.execute('''CREATE TABLE IF NOT EXISTS note (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_etudiant INTEGER,
    note REAL,
    FOREIGN KEY (id_etudiant) REFERENCES etudiant(id)
)''')

# CREATION ADMIN (si inexistant)
c.execute("SELECT COUNT(*) FROM admin WHERE username = ?", ("admin",))
if c.fetchone()[0] == 0:
    password_hash = bcrypt.hashpw("1234".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    c.execute("INSERT INTO admin (username, password) VALUES (?, ?)",
              ("admin", password_hash))

    print("✅ Admin créé (admin / 1234)")
else:
    print("ℹ️ Admin existe déjà")

conn.commit()
conn.close()

print("✅ Base prête !")