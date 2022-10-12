import os
import pytest
import sqlite3
import pickle
from pathlib import Path
from pdfshelf.database import BookDBHandler, FolderDBHandler
from pdfshelf.domain import Book

@pytest.fixture
def rootdir():
    return os.path.dirname(os.path.abspath(__file__))

@pytest.fixture
def db_con():
    con = sqlite3.connect(':memory:')
    con.row_factory = sqlite3.Row
    yield con
    con.close()


@pytest.fixture
def setup_db(db_con, rootdir):
    cur = db_con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS Folder (
                        folder_id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        path TEXT NOT NULL,
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

    pkl_data = Path(rootdir) / "test_data" / "dummie_data.pkl"
    
    with open(pkl_data, 'rb') as inp:
        data = pickle.load(inp)
        books = data["books"]
        folders = data["folders"]

    for book in books:
        cur.execute("""INSERT INTO Book VALUES(NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                            (
                                book["title"],
                                book["authors"],
                                book["year"],
                                book["lang"],
                                book["filename"],
                                book["ext"],
                                book["storage_path"],
                                book["folder_id"],
                                book["size"],
                                book["tags"],
                                book["added_date"],
                                book["hash_id"],
                                book["publisher"],
                                book["isbn13"],
                                book["parsed_isbn"],
                                book["active"],
                                book["confirmed"]
                            ))
        db_con.commit()

    for folder in folders:
        cur.execute("""INSERT INTO Folder VALUES(NULL, ?, ?, ?, ?)""", 
                        (
                            folder["name"],
                            folder["path"],
                            folder["added_date"],
                            folder["active"]
                        ))
        db_con.commit()
class TestBookDBHandler:

    @pytest.mark.usefixtures("setup_db")
    def test_load_all_books(self, db_con) -> None:
        handler = BookDBHandler(db_con)
        books = handler.load_books()

        assert len(books) == 13
    
    # @pytest.mark.usefixtures("setup_db")
    # def test_insert_book(db_con, rootdir) -> None:
    #     handler = BookDBHandler(db_con)

    #     folder = {
    #         "name": "Default",
    #         "path": Path(rootdir)
    #     }
    #     book = Book(
    #         title="Automate the boring stuff with Python",
    #         authors=["Al Sweigart"],
    #         year=2015,
    #         publisher="No Starch Press",
    #         lang="en",
    #         isbn13="9781593275990",
    #         isbn10=None,
    #         parsed_isbn="9781593275990",
    #         folder=folder,
    #         size=78000,
    #         tags=[],
    #         filename="automate-the-boring-stuff.pdf",
    #         ext=".pdf",
    #         storage_path="pythonbooks/automate-the-boring-stuff.pdf",
    #     )

    #     handler.insert_book(book)

        


# Test table creation

# Test insert Book

# Test insert books from list of Books

# Test retrieve books from database

# Test retrieve a book from database

# Test update book

# Test delete book

# Test create folder

# Test retrieve folder

# Test retrieve folders

# Test update folder

# Test delete folder