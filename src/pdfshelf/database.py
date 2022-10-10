import sqlite3
from .config import default_document_folder

Connection = sqlite3.Connection

class DatabaseConnector:

    DB_PATH = default_document_folder / "pdfshelf.db"

    def __init__(self):
        self.con = sqlite3.connect(self.DB_PATH)
        self.create_tables()

    def __enter__(self):
        return self.con

    def __exit__(self, ctx_type, ctx_value, ctx_traceback):
        self.con.close()

    def create_tables(self) -> None:
        cur = self.con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS Folder (
                        folder_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        path TEXT NOT NULL,
                        active INTEGER NOT NULL
                        )""")
        
        cur.execute("""CREATE TABLE IF NOT EXISTS Book (
                        book_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        authors TEXT,
                        year INTEGER,
                        lang TEXT,
                        filename TEXT NOT NULL,
                        ext TEXT NOT NULL,
                        storage_path TEXT NOT NULL,
                        folder_id INTEGER NOT NULL,
                        size REAL NOT NULL,
                        tags TEXT,
                        added_date TEXT NOT NULL,
                        hash_id TEXT NOT NULL UNIQUE,
                        active INTEGER NOT NULL,
                        confirmed INTEGER NOT NULL,
                        FOREIGN KEY (folder_id) REFERENCES Folder (folder_id)
                        )""")




# https://docs.python.org/3/library/sqlite3.html#sqlite3-tutorial
        