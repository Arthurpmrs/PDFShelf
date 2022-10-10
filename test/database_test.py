import os
import pytest
import sqlite3
import csv
from pathlib import Path
from pdfshelf.database import BookDBHandler, FolderDBHandler
from pdfshelf.domain import Book

@pytest.fixture
def rootdir():
    return os.path.dirname(os.path.abspath(__file__))

@pytest.fixture
def db_con():
    con = sqlite3.connect(':memory:')
    yield con
    con.close()


@pytest.fixture
def setup_db(db_con, rootdir):
    cur = db_con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS Folder (
                        name TEXT NOT NULL,
                        path TEXT NOT NULL,
                        added_date TEXT,
                        active INTEGER NOT NULL
                        )""")
        
    cur.execute("""CREATE TABLE IF NOT EXISTS Book (
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
                    FOREIGN KEY (folder_id) REFERENCES Folder (rowid)
                    )""")

    book_data_csv = Path(rootdir) / "test_data" / "dummie_book_data.csv"
    with open(book_data_csv, newline='\n') as f:
        reader = csv.DictReader(f, delimiter=',')
        for row in reader:
            row["year"] = int(row["year"])
            row["folder_id"] = int(row["folder_id"])
            row["active"] = int(row["active"])
            row["confirmed"] = int(row["confirmed"])
            tup_from_row = tuple(row.values())
            cur.execute("""INSERT INTO Book VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                        (
                            row["title"],
                            row["authors"],
                            row["year"],
                            row["lang"],
                            row["filename"],
                            row["ext"],
                            row["storage_path"],
                            row["folder_id"],
                            row["size"],
                            row["tags"],
                            row["added_date"],
                            row["hash_id"],
                            row["publisher"],
                            row["isbn10"],
                            row["isbn13"],
                            row["parsed_isbn"],
                            row["active"],
                            row["confirmed"]
                        ))
            db_con.commit()


    folder_data_csv = Path(rootdir) / "test_data" / "dummie_folder_data.csv"
    with open(folder_data_csv, newline='\n') as f:
        reader = csv.DictReader(f, delimiter=',')
        for row in reader:
            row["active"] = int(row["active"])
            tup_from_row = tuple(row.values())
            cur.execute("""INSERT INTO Folder VALUES(?, ?, ?, ?)""", 
                        (
                            row["name"],
                            row["path"],
                            row["added_date"],
                            row["active"]
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