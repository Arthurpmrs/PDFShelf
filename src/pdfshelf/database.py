import json
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
                        added_date TEXT,
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
        cur = self.con.cursor()

        res = cur.execute("""SELECT rowid, * FROM Book""")
        books = {}
        for row in res.fetchall():
            # procurar como fazer query dos dois ao mesmo tempo
            folder_res = cur.execute("""SELECT * FROM Folder WHERE rowid = ?""", (row[8],)).fetchone()
            folder = Folder(
                name=folder_res[0],
                path=folder_res[1],
                added_date=folder_res[2],
                active=True if folder_res[3] == 1 else False
            )
            print(type(row[2]))
            print(json.dumps(row[2]))
            # Jogar isso aqui em outra função, pq vai estar sempre repetindo
            books.update({row[0]: Book(
                    title=row[1],
                    authors=json.dumps(row[2]),
                    year=row[3],
                    lang=row[4],
                    filename=row[5],
                    ext=row[6],
                    storage_path=row[7],
                    folder=folder,
                    size=row[9],
                    tags=json.loads(row[10]),
                    added_date=row[11],
                    hash_id=row[12],
                    publisher=row[13],
                    isbn10=None if row[14] else row[14],
                    isbn13=None if row[15] else row[15],
                    parsed_isbn=None if row[16] else row[16],
                    active=True if row[17] == 1 else False,
                    confirmed=True if row[18] == 1 else False
            )})
        for book_id, book in books.items():
            print(book)
        return books

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
        