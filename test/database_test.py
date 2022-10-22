import os
import pytest
import sqlite3
import pickle
from datetime import datetime
from pathlib import Path
from pdfshelf.database import BookDBHandler, DatabaseConnector
from pdfshelf.domain import Book
from pdfshelf.config import default_document_folder

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
    DatabaseConnector.create_tables(db_con)  
    pkl_data = Path(rootdir) / "test_data" / "dummie_data.pkl"
    
    with open(pkl_data, 'rb') as inp:
        data = pickle.load(inp)
        books = data["books"]
        folders = data["folders"]

    for book in books:
        cur.execute("""INSERT INTO Book VALUES(NULL, :title, :authors, :year, :lang, :filename, :ext, :storage_path,
                                               :folder_id, :size, :tags, :added_date, :hash_id, :publisher, :isbn13,
                                               :parsed_isbn, :active, :confirmed)""", book)
        db_con.commit()

    for folder in folders:
        cur.execute("""INSERT INTO Folder VALUES(NULL, :name, :path, :added_date, :active)""", folder)
        db_con.commit()
class TestBookDBHandler:

    @pytest.mark.usefixtures("setup_db")
    def test_insert_new_book_existing_folder(self, db_con) -> None:
        handler = BookDBHandler(db_con)

        folder = {
            "name": "Default",
            "path": default_document_folder
        }
        book = Book(
            title="Automate the boring stuff with Python",
            authors=["Al Sweigart"],
            year=2015,
            publisher="No Starch Press",
            lang="en",
            isbn13="9781593275990",
            parsed_isbn="9781593275990",
            folder=folder,
            size=78000,
            tags=[],
            filename="automate-the-boring-stuff.pdf",
            ext=".pdf",
            storage_path="pythonbooks/automate-the-boring-stuff.pdf",
        )

        handler.insert_book(book)

        cur = db_con.cursor()
        book_count = cur.execute("SELECT count(*) from Book").fetchall()[0][0]
        folder_count = cur.execute("SELECT count(*) from Folder").fetchall()[0][0]

        assert book_count == 14
        assert folder_count == 3


    @pytest.mark.usefixtures("setup_db")
    def test_load_all_books(self, db_con) -> None:
        handler = BookDBHandler(db_con)
        books = handler.load_books()
        
        for b in books.values():
            book = b
            break

        assert len(books) == 13
        assert isinstance(book.authors, list) == True
        assert isinstance(book.tags, list) == True
        assert isinstance(book.added_date, datetime) == True
        assert isinstance(book.confirmed, bool) == True
        assert isinstance(book.active, bool) == True
        assert isinstance(book.storage_path, Path) == True
        assert isinstance(book.folder.path, Path) == True
        assert isinstance(book.folder.active, bool) == True
        assert isinstance(book.folder.added_date, datetime) == True


    # @pytest.mark.usefixtures("setup_db")
    # def test_load_all_books_even_without_folder(self, db_con) -> None:
    #     cur = db_con.cursor()
        
    #     cur.execute()

        


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