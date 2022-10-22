import json
import sqlite3
from .domain import Book, Folder
from .config import default_document_folder

Connection = sqlite3.Connection

class DatabaseConnector:

    DB_PATH = default_document_folder / "pdfshelf.db"

    def __init__(self):
        self.con = sqlite3.connect(self.DB_PATH)
        self.con.row_factory = sqlite3.Row
        DatabaseConnector.create_tables(self.con)

    def __enter__(self):
        return self.con

    def __exit__(self, ctx_type, ctx_value, ctx_traceback):
        self.con.close()

    @staticmethod
    def create_tables(con) -> None:
        cur = con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS Folder (
                        folder_id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL UNIQUE,
                        path TEXT NOT NULL UNIQUE,
                        added_date TEXT,
                        active INTEGER NOT NULL
                        )""")
        
        cur.execute("""CREATE TABLE IF NOT EXISTS Book (
                        book_id INTEGER PRIMARY KEY,
                        title TEXT,
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
        cur = self.con.cursor()

        parsed_book, parsed_folder = book.get_parsed_dict()

        cur.execute("""INSERT OR IGNORE INTO Folder VALUES(:folder_id, :name, :path, :added_date, :active)""", parsed_folder)

        if parsed_book["folder_id"] is None:
            parsed_book["folder_id"] = cur.lastrowid 

        cur.execute("""INSERT OR IGNORE INTO Book VALUES(:book_id, :title, :authors, :year, :lang, :filename, :ext, :storage_path, 
                                               :folder_id, :size, :tags, :added_date, :hash_id, :publisher, :isbn13,
                                               :parsed_isbn, :active, :confirmed)""", parsed_book)
        
    def insert_books(self, books: list[Book]) -> None:
        pass

    def load_books(self, sorting_key: str = "no_sorting", filter_key: str = "no_filter", filter_content: str = None) -> dict[int, Book]:
        cur = self.con.cursor()

        res = cur.execute("""SELECT * FROM Book
                             LEFT JOIN Folder 
                             ON Book.folder_id == Folder.folder_id""")        
        books = {}
        for row in res.fetchall():
            book_dict = {k:v for k, v in zip(row.keys()[0:18], row[0:18])}
            book_dict.pop("folder_id")

            folder_dict = {k:v for k, v in zip(row.keys()[18:23], row[18:23])}
            folder = Folder(**folder_dict)

            books.update(
                {row["book_id"]: Book(**book_dict, folder=folder)}
            )
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
        