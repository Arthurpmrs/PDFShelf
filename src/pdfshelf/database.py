import json
import time
import sqlite3
import logging
import traceback
from typing import Any
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
        """Insert a list of Book objects into Book table."""

        try:
            cur = self.con.cursor()
            self.logger.info(f"Transaction started")

            book_id, folder_id = self._insert_single_book(book, cur)

            self.con.commit()
            self.logger.info(f"Transaction ended successfully!")
        except sqlite3.Error:
            self.logger.error(
                "Transaction failed, rolling back!\n"
                f"{traceback.format_exc()}"
            )
            self.con.rollback()
            return -1, -1

        return book_id, folder_id

    def insert_books(self, books: list[Book]) -> None:
        """Insert a single Book object into Book table."""

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
            self.logger.error(
                "Transaction failed, rolling back!\n"
                f"{traceback.format_exc()}"
            )
            self.con.rollback()

    def _insert_single_book(self, book: Book, cur: sqlite3.Cursor) -> tuple[int, int]:
        """Inserts Book into Book table if not Duplicate."""

        if book is None:
            self.logger.error("None Book passed!")
            raise TypeError("Can not insert a None Book!")

        parsed_book, parsed_folder = book.get_parsed_dict()

        folder_status = "ADDED"
        try:
            values = ":folder_id, :name, :path, :added_date, :active"
            cur.execute(f"INSERT INTO Folder VALUES({values})", parsed_folder)
        except sqlite3.IntegrityError:
            folder_status = "ALREADY EXISTS"

        folder_id = cur.execute(
            "SELECT folder_id FROM Folder WHERE name = ?;",
            (book.folder.name,)
        ).fetchone()[0]
        parsed_book["folder_id"] = folder_id

        self.logger.debug(f"    "
                          f"[{folder_status}] Folder {book.folder.name} "
                          f"(ID = {folder_id})")

        is_duplicate = False
        try:
            values = """:book_id, :title, :authors, :year, :lang, :filename, 
                        :ext, :storage_path, :folder_id, :size, :tags, 
                        :added_date, :hash_id, :publisher, :isbn13, :parsed_isbn, 
                        :active, :confirmed"""
            cur.execute(f"INSERT INTO Book VALUES({values})", parsed_book)

            self.logger.info(f"    "
                             f"[ADDED] Book \"{book.get_short_filename()}\"")
        except sqlite3.IntegrityError:
            is_duplicate = True

        book_id = cur.execute("""SELECT book_id 
                                 FROM Book 
                                 WHERE hash_id = ? OR 
                                 (isbn13 = ? AND isbn13 IS NOT NULL)""",
                              (book.hash_id, book.isbn13, )
                              ).fetchone()[0]

        if is_duplicate:
            self._insert_duplicate_book(
                cur, book_id, parsed_book, book.get_short_filename()
            )

        return book_id, folder_id

    def _insert_duplicate_book(
        self, cur: sqlite3.Cursor, book_id: int, parsed_book: dict,
        short_name: str
    ) -> None:
        """Inserts duplicate book on Duplicate table."""

        parsed_book.pop("book_id")
        parsed_book.update({"original_book_id": book_id})

        values = """:original_book_id, :title, :authors, :year, :lang, 
                    :filename, :ext, :storage_path, :folder_id, :size, 
                    :tags, :added_date, :hash_id, :publisher, :isbn13,
                    :parsed_isbn"""
        cur.execute(f"INSERT INTO Duplicate VALUES({values})", parsed_book)

        self.logger.warning(f"    "
                            f"[DUPLICATE] "
                            f"\"{short_name}\" equal to Book {book_id}")

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

    def load_books(
        self, sorting_key: str = "no_sorting", filter_key: str = "no_filter",
        filter_content: Any = ""
    ) -> list[Book]:
        """
        Read Books from Database.

        Sorting by: title, added_date, year and size.
        Filtering by: publisher, author, tag, ext, year, active and confirmed.
        """

        cur = self.con.cursor()
        sorting = {
            "no_sorting": "",
            "title": " ORDER BY title NULLS LAST",
            "added_date": " ORDER BY added_date",
            "year": " ORDER BY year NULLS LAST",
            "size": " ORDER BY size"
        }
        filtering = {
            "no_filter": " WHERE Book.hash_id != ?",
            "publisher": " WHERE Book.publisher == ?",
            "ext": " WHERE Book.ext == ?",
            "year": " WHERE Book.year == ?",
            "tag": " WHERE Book.tags LIKE ?",
            "active": " WHERE Book.active == ?",
            "confirmed": " WHERE Book.confirmed == ?",
            "author": " WHERE Book.authors LIKE ?"
        }

        if filter_key == "tag" or filter_key == "author":
            filter_content = f"%{filter_content}%"

        query = ("""SELECT * FROM Book
                    LEFT JOIN Folder 
                    ON Book.folder_id == Folder.folder_id"""
                 + filtering[filter_key]
                 + sorting[sorting_key])
        res = cur.execute(query, (filter_content, ))

        books = []
        for row in res.fetchall():
            book = self._get_book_from_row(row)
            books.append(book)

        filtered_message = "All Books"
        if filter_key != "no_filter":
            filtered_message = f"Books filtered by {filter_key}"

        sorted_message = ""
        if sorting_key != "no_sorting":
            sorted_message = f", ordered by {sorting_key}"

        self.logger.debug(f"[SELECTED] {filtered_message}{sorted_message}")

        return books

    def _get_book_from_row(self, row: sqlite3.Row) -> Book:
        book_dict = {k: v for k, v in zip(row.keys()[0:18], row[0:18])}
        book_dict.pop("folder_id")

        folder_dict = {k: v for k, v in zip(row.keys()[18:23], row[18:23])}
        folder = Folder(**folder_dict)

        return Book(**book_dict, folder=folder)

    def update_book(self, book_id: int, content: dict[str, str]) -> bool:
        """Update a Book by passing the modified properties and their values."""

        if len(content) == 0:
            self.logger.warning("No value update value passed!")
            return False

        cur = self.con.cursor()
        values = list(content.values())
        set_statement = "SET "

        for i, key in enumerate(content):
            if BookDBHandler._is_protected(key):
                self.logger.error(
                    f"'{key}' cannot be changed! Operation canceled!"
                )
                raise ValueError(f"{key} cannot be changed by this method!")

            if (i + 1) == len(content):
                set_statement += f"{key} = ?"
            else:
                set_statement += f"{key} = ?, "

        query = f"""
                UPDATE Book
                {set_statement}
                WHERE Book.book_id = ?
                """

        try:
            cur.execute(query, (*values, book_id, ))
        except sqlite3.OperationalError:
            self.logger.error(
                f"Column does not exist ({', '.join(list(content.keys()))})\n"
                f"{traceback.format_exc()}"
            )
            return False
        except sqlite3.Error:
            self.logger.error(
                "Update failed!\n"
                f"{traceback.format_exc()}"
            )
            return False
        self.con.commit()

        content_msg = '\n'.join([f'{k} = {v}' for k, v in content.items()])
        self.logger.debug(
            f"[UPDATED] Book {book_id} with following values:\n"
            f"{content_msg}"
        )
        return True

    @staticmethod
    def _is_protected(key: str) -> bool:
        protected_fields = [
            "book_id", "filename", "ext", "storage_path", "folder_id", "size",
            "added_date", "hash_id", "isbn13", "parsed_isbn", "active",
            "confirmed"
        ]
        return True if key in protected_fields else False

    def delete_book(self, book_id: int) -> bool:
        """Delete one Book from Book table."""

        cur = self.con.cursor()
        try:
            cur.execute("DELETE from Book WHERE Book.book_id = ?", (book_id, ))
            self.con.commit()
        except sqlite3.Error:
            self.logger.error(
                "Deletion failed!\n"
                f"{traceback.format_exc()}"
            )
            return False

        self.logger.debug(f"[DELETED] Book {book_id}.")
        return True


class FolderDBHandler:

    def __init__(self, con: Connection) -> None:
        self.con = con
        self.logger = logging.getLogger(__name__)

    def insert_folder(self, folder: Folder) -> int:
        """Insert new Folder to the Database. Returns folder_id."""
        if folder is None:
            self.logger.error("None Folder passed!")
            raise TypeError("Can not insert a None Folder!")

        parsed_folder = folder.get_parsed_dict()
        folder_status = "ADDED"
        try:
            values = ":folder_id, :name, :path, :added_date, :active"
            query = f"INSERT INTO Folder VALUES({values})"
            self.con.execute(query, parsed_folder)
        except sqlite3.IntegrityError:
            folder_status = "ALREADY EXISTS"

        select_query = """
                       SELECT folder_id
                       FROM Folder
                       WHERE Folder.name = ?
                       """
        folder_id = (self.con.execute(select_query, (folder.name, ))
                     .fetchone()[0])

        self.logger.debug(f"[{folder_status}] Folder \"{folder.name}\" "
                          f"(ID = {folder_id})")

        return folder_id

    def load_folder_by_id(self, folder_id: int) -> Folder:
        """Load one Folder given a ID."""

        query = """
                SELECT * FROM Folder    
                WHERE Folder.folder_id = ?
                """

        res = self.con.execute(query, (folder_id, ))

        row = res.fetchone()
        if row is None:
            self.logger.error(f"Folder ID {folder_id} doest not exist!")
            raise ValueError(f"Folder ID {folder_id} doest not exist!")

        folder = Folder(**{k: v for k, v in zip(row.keys(), row)})
        self.logger.debug(f"[SELECTED] Folder \"{folder.name}\"")
        return folder

    def load_folders(
        self, sorting_key: str = "no_sorting", filter_key: str = "no_filter"
    ) -> list[Folder]:
        """
        Read Folders from Database.

        Sorting by: name, added_date and path.
        Filtering by: active and not_active.
        """

        sorting = {
            "no_sorting": "",
            "name": "ORDER BY Folder.name",
            "date": "ORDER BY Folder.added_date",
            "path": "ORDER BY Folder.path"
        }
        filtering = {
            "no_filter": "",
            "active": "WHERE Folder.active == 1",
            "not_active": "WHERE Folder.active == 0"
        }
        query = f"""
                SELECT * FROM Folder
                {filtering[filter_key]}
                {sorting[sorting_key]}
                """
        res = self.con.execute(query)

        folders = []
        for row in res.fetchall():
            folder = Folder(**{k: v for k, v in zip(row.keys(), row)})
            folders.append(folder)

        return folders

    def update_folder(self, folder_id: int) -> None:
        pass

    def delete_folder(self, folder_id: int) -> None:
        pass


class DuplicateDBHandler:
    pass
# https://docs.python.org/3/library/sqlite3.html#sqlite3-tutorial
