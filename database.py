import sqlite3
import datetime

DB_PATH = "donnees_locales.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = ON')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS utilisateurs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        date_creation TEXT,
        terms_accepted INTEGER NOT NULL DEFAULT 0
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS historique (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        question TEXT,
        reponse TEXT,
        source TEXT,
        date TEXT,
        FOREIGN KEY(user_id) REFERENCES utilisateurs(id)
    )''')

    cur.execute("PRAGMA table_info(historique)")
    columns = [row[1] for row in cur.fetchall()]
    if 'user_id' not in columns:
        cur.execute('ALTER TABLE historique ADD COLUMN user_id INTEGER')

    cur.execute("PRAGMA table_info(utilisateurs)")
    user_columns = [row[1] for row in cur.fetchall()]
    if 'terms_accepted' not in user_columns:
        cur.execute('ALTER TABLE utilisateurs ADD COLUMN terms_accepted INTEGER NOT NULL DEFAULT 0')
    if 'role' not in user_columns:
        cur.execute("ALTER TABLE utilisateurs ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")

    conn.commit()
    conn.close()


def get_user_stats():
    """Retourne les métadonnées utilisateurs sans aucun contenu de message (RGPD)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('''
        SELECT u.id, u.nom, u.email, u.date_creation, u.role,
               COUNT(h.id)  AS nb_conversations,
               MAX(h.date)  AS derniere_activite
        FROM utilisateurs u
        LEFT JOIN historique h ON h.user_id = u.id
        GROUP BY u.id
        ORDER BY u.date_creation DESC
    ''')
    rows = cur.fetchall()
    conn.close()
    return rows

def creer_utilisateur(nom, email, password_hash):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute(
            'INSERT INTO utilisateurs (nom, email, password_hash, date_creation) VALUES (?,?,?,?)',
            (nom, email, password_hash, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_utilisateur_par_email(email):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('SELECT * FROM utilisateurs WHERE email = ?', (email,))
    row = cur.fetchone()
    conn.close()
    return row

def chercher_question(question, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if user_id is not None:
        cur.execute(
            'SELECT * FROM historique WHERE question = ? AND user_id = ? LIMIT 1',
            (question, user_id),
        )
    else:
        cur.execute('SELECT * FROM historique WHERE question = ? LIMIT 1', (question,))
    row = cur.fetchone()
    conn.close()
    return row


def get_utilisateur_par_id(user_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('SELECT * FROM utilisateurs WHERE id = ?', (user_id,))
    row = cur.fetchone()
    conn.close()
    return row

def mettre_a_jour_utilisateur(user_id, nom, email, password_hash=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        if password_hash:
            cur.execute(
                'UPDATE utilisateurs SET nom = ?, email = ?, password_hash = ? WHERE id = ?',
                (nom, email, password_hash, user_id)
            )
        else:
            cur.execute(
                'UPDATE utilisateurs SET nom = ?, email = ? WHERE id = ?',
                (nom, email, user_id)
            )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def definir_acceptation_conditions(user_id, acceptees=True):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        'UPDATE utilisateurs SET terms_accepted = ? WHERE id = ?',
        (1 if acceptees else 0, user_id),
    )
    conn.commit()
    conn.close()

def sauvegarder(question, reponse, source, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO historique (user_id, question, reponse, source, date) VALUES (?,?,?,?,?)',
        (
            user_id,
            question,
            reponse,
            source,
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        ),
    )
    conn.commit()
    conn.close()

def get_historique(user_id=None, limit=50):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if user_id is not None:
        cur.execute(
            'SELECT id, question, reponse, source, date FROM historique WHERE user_id = ? ORDER BY id DESC LIMIT ?',
            (user_id, limit),
        )
    else:
        cur.execute(
            'SELECT id, question, reponse, source, date FROM historique ORDER BY id DESC LIMIT ?',
            (limit,),
        )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_historique_chronologique(user_id=None, limit=50):
    rows = get_historique(user_id, limit)
    return list(reversed(rows))


def get_historique_depuis(user_id, date_debut):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        'SELECT id, question, reponse, source, date FROM historique WHERE user_id = ? AND date >= ? ORDER BY id ASC',
        (user_id, date_debut),
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def supprimer_discussion(discussion_id, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if user_id is not None:
        cur.execute(
            'DELETE FROM historique WHERE id = ? AND user_id = ?',
            (discussion_id, user_id),
        )
    else:
        cur.execute('DELETE FROM historique WHERE id = ?', (discussion_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted
