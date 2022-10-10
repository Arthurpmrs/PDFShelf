import sqlite3
from .domain import Book, Folder
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
                        publisher TEXT,
                        isbn10 TEXT,
                        isbn13 TEXT,
                        parsed_isbn TEXT,
                        active INTEGER NOT NULL,
                        confirmed INTEGER NOT NULL,
                        FOREIGN KEY (folder_id) REFERENCES Folder (folder_id)
                        )""")


class BookDBHandler:

    def __init__(self, con: Connection) -> None:
        self.con = con
    
    def insert_book(self, book: Book) -> None:
        pass

    def insert_books(self, books: list[Book]) -> None:
        pass

    def load_books(self, sorting_key: str = "title", filter_key: str = "no_filter", filter_content: str = None) -> dict[int, Book]:
        pass

    def load_book_by_id(self, book_id: int) -> Book:
        pass

    def update_book(self, book_id: int, content: dict[str, str]) -> None:
        pass

    def delete_book(self, book_id: int) -> None:
        pass


class FolderDBHandler:

    def __init__(self, con: Connection) -> None:
        self.con = con

    def insert_folder(self, folder: Folder) -> None:
        pass

    def load_folders(self, sorting_key: str = "added_date", filter_key: str = "no_filter", filter_content: str = None) -> dict[int, Folder]:
        pass

    def update_folder(self, folder_id: int) -> None:
        pass

    def delete_folder(self, folder_id: int) -> None:
        pass




# https://docs.python.org/3/library/sqlite3.html#sqlite3-tutorial
        