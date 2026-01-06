import sqlite3


conn = sqlite3.connect("storage.db", check_same_thread=False)
cur = conn.cursor()


cur.execute("""
CREATE TABLE IF NOT EXISTS chats (
id INTEGER PRIMARY KEY AUTOINCREMENT,
session_id TEXT,
role TEXT,
message TEXT
)
""")


cur.execute("""
CREATE TABLE IF NOT EXISTS documents (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
content TEXT
)
""")


conn.commit()