import os
import pytest
import sqlite3
import pickle
from datetime import datetime
from pathlib import Path
from pdfshelf.database import BookDBHandler, DatabaseConnector
from pdfshelf.domain import Book, Folder
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
        book_id, folder_id = handler.insert_book(book)

        cur = db_con.cursor()
        book_count = cur.execute("SELECT count(*) from Book").fetchall()[0][0]
        folder_count = cur.execute("SELECT count(*) from Folder").fetchall()[0][0]

        assert book_id == 14
        assert folder_id == 3
        assert book_count == 14
        assert folder_count == 3
    
    @pytest.mark.usefixtures("setup_db")
    def test_insert_existing_book_new_folder(self, db_con) -> None:
        handler = BookDBHandler(db_con)

        folder = {
            "name": "folder-3",
            "path": "/home/arthurpmrs/Documents/Library/dummie-data-source/folder-3"
        }
        book = Book(
            title="Artificial Intelligence With Python",
            authors=["Prateek Joshi"],
            year=2017,
            publisher="No Starch Press",
            lang="en",
            isbn13="9781786464392",
            parsed_isbn="978-1-78646-439-2",
            folder=folder,
            size=78000,
            tags=[],
            filename="Prateek Joshi-Artificial Intelligence with Python-Packt Publishing - ebooks Account (2017).epub",
            ext=".epub",
            storage_path="pythonbooks/Prateek Joshi-Artificial Intelligence with Python-Packt Publishing - ebooks Account (2017).epub",
        )
        book_id, folder_id = handler.insert_book(book)

        cur = db_con.cursor()
        book_count = cur.execute("SELECT count(*) from Book").fetchall()[0][0]
        folder_count = cur.execute("SELECT count(*) from Folder").fetchall()[0][0]
        
        assert book_id == 1
        assert folder_id == 4
        assert book_count == 13
        assert folder_count == 4

    @pytest.mark.usefixtures("setup_db")
    def test_data_integrity_after_insert(self, db_con) -> None:
        handler = BookDBHandler(db_con)

        folder = {
            "name": "folder-3",
            "path": "/home/arthurpmrs/Documents/Library/dummie-data-source/folder-3"
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

        book_id, _ = handler.insert_book(book)
        loaded_book = handler.load_book_by_id(book_id)

        assert isinstance(loaded_book.authors, list) == True
        assert isinstance(loaded_book.tags, list) == True
        assert isinstance(loaded_book.added_date, datetime) == True
        assert isinstance(loaded_book.confirmed, bool) == True
        assert isinstance(loaded_book.active, bool) == True
        assert isinstance(loaded_book.size, float) == True
        assert isinstance(loaded_book.storage_path, Path) == True
        assert isinstance(loaded_book.folder, Folder) == True
        assert isinstance(loaded_book.folder.path, Path) == True  # type: ignore
        assert isinstance(loaded_book.folder.active, bool) == True # type: ignore
        assert isinstance(loaded_book.folder.added_date, datetime) == True # type: ignore

    @pytest.mark.usefixtures("setup_db")
    def test_insert_none(self, db_con) -> None:
        handler = BookDBHandler(db_con)
        book = None
        with pytest.raises(TypeError):
            handler.insert_book(book) # type: ignore

    @pytest.mark.usefixtures("setup_db")
    def test_load_all_books(self, db_con) -> None:
        handler = BookDBHandler(db_con)
        books = handler.load_books()
        
        assert len(books) == 13


    @pytest.mark.usefixtures("setup_db")
    def test_insert_books(self, db_con) -> None:
        handler = BookDBHandler(db_con)
        books = [
            Book(
                title="Automate the boring stuff with Python",
                authors=["Al Sweigart"],
                year=2015,
                publisher="No Starch Press",
                lang="en",
                isbn13="9781593275990",
                parsed_isbn="9781593275990",
                folder={
                    "name": "folder-3",
                    "path": "/home/arthurpmrs/Documents/Library/dummie-data-source/folder-3"
                },
                size=78000,
                tags=[],
                filename="automate-the-boring-stuff.pdf",
                ext=".pdf",
                storage_path="pythonbooks/automate-the-boring-stuff.pdf",
        ),
            Book(
                title="Python Crash Course",
                authors=["Eric Matthes"],
                year=2016,
                publisher="No Starch Press",
                lang="en",
                isbn13="9781593276034",
                parsed_isbn="9781593276034",
                folder={
                    "name": "folder-3",
                    "path": "/home/arthurpmrs/Documents/Library/dummie-data-source/folder-3"
                },
                size=150000,
                tags=[],
                filename="python-crash-course.pdf",
                ext=".pdf",
                storage_path="pythonbooks/python-crash-course.pdf",
        ),
            Book(
                title="Artificial Intelligence With Python",
                authors=["Prateek Joshi"],
                year=2017,
                publisher="No Starch Press",
                lang="en",
                isbn13="9781786464392",
                parsed_isbn="978-1-78646-439-2",
                folder={
                    "name": "Default",
                    "path": default_document_folder
                },
                size=78000,
                tags=[],
                filename="Prateek Joshi-Artificial Intelligence with Python-Packt Publishing - ebooks Account (2017).epub",
                ext=".epub",
                storage_path="pythonbooks/Prateek Joshi-Artificial Intelligence with Python-Packt Publishing - ebooks Account (2017).epub",
            ),
            Book(
                title="Fluent Python 2ed",
                authors=["Luciano Ramalho"],
                year=2022,
                publisher="O'Reilly Media",
                lang="en",
                isbn13="9781492056355",
                parsed_isbn="9781492056355",
                folder={
                    "name": "folder-4",
                    "path": "/home/arthurpmrs/Documents/Library/dummie-data-source/folder-4"
                },
                size=78000,
                tags=[],
                filename="fluent-python-2.epub",
                ext=".epub",
                storage_path="pythonbooks/fluent-python-2.epub",
            )
        ]
        handler.insert_books(books)

        cur = db_con.cursor()
        book_count = cur.execute("SELECT count(*) from Book").fetchall()[0][0]
        folder_count = cur.execute("SELECT count(*) from Folder").fetchall()[0][0]

        assert book_count == 16
        assert folder_count == 5

    @pytest.mark.usefixtures("setup_db")
    def test_insert_books_empty_list(self, db_con) -> None:
        handler = BookDBHandler(db_con)
        result = handler.insert_books([])
        assert result == None
        # with pytest.raises(ValueError):
        #     handler.insert_books([])



        


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