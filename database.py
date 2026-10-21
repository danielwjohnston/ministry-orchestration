import sqlite3
import os

def get_db_path():
    return os.environ.get("BODY_ORCH_DB", "body_orchestrator.db")

def get_connection():
    """
    Returns a secure SQLite connection.
    Enforces foreign keys and ensures the file permissions are aggressively set to 600.
    """
    db_path = get_db_path()
    
    # Create DB file if it doesn't exist
    if not os.path.exists(db_path):
        open(db_path, 'a').close()
        
    # ALWAYS enforce secure permissions, even if pre-created by an attacker
    os.chmod(db_path, 0o600)  # User read/write only

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes the required tables with strict UNIQUE constraints for idempotency."""
    conn = get_connection()
    try:
        # Organization table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS organization (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT,
                primary_contact TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # In a real environment we'd use migrations, but for MVP we recreate if we need to enforce constraints.
        conn.execute('''
            CREATE TABLE IF NOT EXISTS ministry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY(org_id) REFERENCES organization(id),
                UNIQUE(org_id, name)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS capability (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY(org_id) REFERENCES organization(id),
                UNIQUE(org_id, category)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS need (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY(org_id) REFERENCES organization(id),
                UNIQUE(org_id, category)
            )
        ''')
        
        # Insert a default Organization 001 if empty
        cursor = conn.execute("SELECT count(*) as cnt FROM organization")
        if cursor.fetchone()['cnt'] == 0:
            conn.execute('''
                INSERT INTO organization (name) VALUES (?)
            ''', ("Connection Christian Church",))
        
        conn.commit()
    finally:
        conn.close()

def get_all_organizations():
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM organization ORDER BY name").fetchall()
    finally:
        conn.close()

def get_organization(org_id):
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT * FROM organization WHERE id = ?", (org_id,))
        return cursor.fetchone()
    finally:
        conn.close()

def create_organization(name):
    conn = get_connection()
    try:
        cursor = conn.execute("INSERT INTO organization (name) VALUES (?)", (name,))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def update_organization(org_id, name, address, primary_contact):
    conn = get_connection()
    try:
        conn.execute('''
            UPDATE organization
            SET name = ?, address = ?, primary_contact = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (name, address, primary_contact, org_id))
        conn.commit()
    finally:
        conn.close()

def get_ministries(org_id):
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM ministry WHERE org_id = ?", (org_id,)).fetchall()
    finally:
        conn.close()

def add_ministry(org_id, name, description):
    conn = get_connection()
    try:
        conn.execute("INSERT OR IGNORE INTO ministry (org_id, name, description) VALUES (?, ?, ?)", (org_id, name, description))
        conn.commit()
    finally:
        conn.close()

def get_capabilities(org_id):
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM capability WHERE org_id = ?", (org_id,)).fetchall()
    finally:
        conn.close()

def add_capability(org_id, category, description):
    conn = get_connection()
    try:
        conn.execute("INSERT OR IGNORE INTO capability (org_id, category, description) VALUES (?, ?, ?)", (org_id, category, description))
        conn.commit()
    finally:
        conn.close()

def get_needs(org_id):
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM need WHERE org_id = ?", (org_id,)).fetchall()
    finally:
        conn.close()

def add_need(org_id, category, description):
    conn = get_connection()
    try:
        conn.execute("INSERT OR IGNORE INTO need (org_id, category, description) VALUES (?, ?, ?)", (org_id, category, description))
        conn.commit()
    finally:
        conn.close()

def get_orchestration_matches():
    """
    Returns pairings where Organization A has a Need that matches Organization B's Capability.
    """
    conn = get_connection()
    try:
        query = '''
        SELECT 
            n.org_id as need_org_id,
            org_n.name as need_org_name,
            n.category as shared_category,
            n.description as need_description,
            c.org_id as cap_org_id,
            org_c.name as cap_org_name,
            c.description as cap_description
        FROM need n
        JOIN capability c ON lower(n.category) = lower(c.category) AND n.org_id != c.org_id
        JOIN organization org_n ON n.org_id = org_n.id
        JOIN organization org_c ON c.org_id = org_c.id
        ORDER BY n.category
        '''
        return conn.execute(query).fetchall()
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()
    print(f"Database initialized securely at {get_db_path()}")
