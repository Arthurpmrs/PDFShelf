import json
import time
import sqlite3
import logging
import traceback
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
                        added_date DATE,
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
                        added_date DATE NOT NULL,
                        hash_id TEXT NOT NULL UNIQUE,
                        publisher TEXT,
                        isbn13 TEXT UNIQUE,
                        parsed_isbn TEXT,
                        active INTEGER NOT NULL,
                        confirmed INTEGER NOT NULL,
                        FOREIGN KEY (folder_id) REFERENCES Folder (folder_id)
                        )""")
    
        cur.execute("""CREATE TABLE IF NOT EXISTS Duplicate (
                        original_book_id INTEGER NOT NULL,
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
                        added_date DATE NOT NULL,
                        hash_id TEXT NOT NULL,
                        publisher TEXT,
                        isbn13 TEXT,
                        parsed_isbn TEXT,
                        FOREIGN KEY (original_book_id) REFERENCES Book (book_id),
                        FOREIGN KEY (folder_id) REFERENCES Folder (folder_id)
                        )""")


class BookDBHandler:

    def __init__(self, con: Connection) -> None:
        self.con = con
        self.logger = logging.getLogger(__name__)
    
    def insert_book(self, book: Book) -> tuple[int, int]:
        try: 
            cur = self.con.cursor()
            self.logger.info(f"Transaction started")
            book_id, folder_id = self._insert_single_book(book, cur)
            self.con.commit() 
            self.logger.info(f"Transaction ended successfully!")
        except sqlite3.Error:
            self.logger.error(f"Transaction failed, rolling back!\n{traceback.format_exc()}")
            self.con.rollback()
            return -1, -1
        return book_id, folder_id

    def insert_books(self, books: list[Book]) -> None:
        if len(books) == 0:
            self.logger.warning("Empty Book list was passed!")
            return
        
        self.con.isolation_level = None
        try: 
            cur = self.con.cursor()
            cur.execute("BEGIN")
            self.logger.info(f"Transaction started")
            for book in books:
                self._insert_single_book(book, cur)
            self.con.commit()
            self.logger.info(f"Transaction ended successfully!")
        except sqlite3.Error:
            self.logger.error(f"Transaction failed, rolling back!\n{traceback.format_exc()}")
            self.con.rollback()
        

    def _insert_single_book(self, book: Book, cur: sqlite3.Cursor) -> tuple[int, int]:
        if book is None:
            self.logger.error("None Book passed!")
            raise TypeError("Can not insert a None Book!")
        
        parsed_book, parsed_folder = book.get_parsed_dict()

        folder_was = "ADDED"
        try:
            cur.execute("""INSERT INTO Folder VALUES(:folder_id, :name, :path, :added_date, :active)""", parsed_folder)
        except sqlite3.IntegrityError as error:
            folder_was = "ALREADY EXISTS"
        
        folder_id = cur.execute("""SELECT folder_id FROM Folder WHERE name = ?;""", (book.folder.name,  )).fetchone()[0]
        self.logger.debug(f"    [{folder_was}] Folder {book.folder.name} (ID = {folder_id})")
        parsed_book["folder_id"] = folder_id

        is_duplicate = False
        try:
            cur.execute("""INSERT INTO Book VALUES(:book_id, :title, :authors, :year, :lang, :filename, :ext, :storage_path, 
                                                :folder_id, :size, :tags, :added_date, :hash_id, :publisher, :isbn13,
                                                :parsed_isbn, :active, :confirmed)""", parsed_book)
            self.logger.info(f"    [ADDED] Book \"{book.get_short_filename()}\"")
        except sqlite3.IntegrityError as error:
            is_duplicate = True
        
        res = cur.execute("""SELECT book_id FROM Book WHERE hash_id = ? OR (isbn13 = ? AND isbn13 IS NOT NULL)""", 
                          (book.hash_id, book.isbn13, )).fetchone()
        book_id = res[0]
        if is_duplicate:
            parsed_book.pop("book_id")
            parsed_book.update({"original_book_id": book_id})
            cur.execute("""INSERT INTO Duplicate VALUES(:original_book_id, :title, :authors, :year, :lang, :filename, :ext, :storage_path, 
                                                :folder_id, :size, :tags, :added_date, :hash_id, :publisher, :isbn13,
                                                :parsed_isbn)""", parsed_book)
            self.logger.warning(f"    [DUPLICATE] \"{book.get_short_filename()}\" equal to Book {book_id}")
        return book_id, folder_id

    def load_books(self, sorting_key: str = "no_sorting", filter_key: str = "no_filter", filter_content: str = None) -> list[Book]:
        cur = self.con.cursor()
        sorting = {
            "no_sorting": "",
            "title": "ORDER BY title NULLS LAST",
            "added_date": "ORDER BY added_date",
            "year": "ORDER BY year NULLS LAST",
            "size": "ORDER BY size"
        }
        res = cur.execute("""SELECT * FROM Book
                             LEFT JOIN Folder 
                             ON Book.folder_id == Folder.folder_id
                             """ + sorting[sorting_key])        
        books = []
        for row in res.fetchall():
            book = self._get_book_from_row(row)
            books.append(book)
        
        if sorting_key == "no_sorting":
            self.logger.debug("[SELECTED] All Books")
        else:
            self.logger.debug(f"[SELECTED] All Books ordered by {sorting_key}")
        return books

    def load_book_by_id(self, book_id: int) -> Book:
        cur = self.con.cursor()

        res = cur.execute("""SELECT * FROM Book
                             LEFT JOIN Folder 
                             ON Book.folder_id == Folder.folder_id
                             WHERE book_id = ?""", (book_id, ))        
        
        row = res.fetchone()
        if row is None:
            raise ValueError("Book ID does not exist!")
        
        book = self._get_book_from_row(row)
        self.logger.debug(f"[SELECTED] Book \"{book.get_short_filename()}\"")

        return book

    def _get_book_from_row(self, row: sqlite3.Row) -> Book:
        book_dict = {k:v for k, v in zip(row.keys()[0:18], row[0:18])}
        book_dict.pop("folder_id")

        folder_dict = {k:v for k, v in zip(row.keys()[18:23], row[18:23])}
        folder = Folder(**folder_dict)

        return Book(**book_dict, folder=folder)

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
        