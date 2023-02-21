import os
import json
import pytest
import sqlite3
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any
from pdfshelf.database import BookDBHandler, DatabaseConnector, FolderDBHandler
from pdfshelf.domain import Book, Folder
from pdfshelf.config import default_document_folder


class _Auto:
    """
    Sentinel value indicating an automatic default will be used.
    Ref: https://lukeplant.me.uk/blog/posts/test-factory-functions-in-django/
    """

    def __bool__(self):
        return False


Auto: Any = _Auto()


def folder_factory(
    *, name: str = "folder-000", path: str = "/home/username/Documents/Books",
    added_date: datetime = Auto, folder_id: int = Auto, active: int = True
) -> Folder:
    folder = Folder.from_raw_data({
        "name": name,
        "path": path,
        "added_date": datetime.now() if added_date is Auto else added_date,
        "folder_id": None if folder_id is Auto else folder_id,
        "active": active
    })
    return folder


def book_factory(
    *, title: str = "TheBookTM", authors: list[str] = Auto, year: int = 2021,
    publisher: str = "ThePublisherTM", lang: str = "en",
    isbn13: str = "9781593275990", parsed_isbn: str = "9781593275990",
    folder: Folder = Auto, size: float = 12001.1, tags: list[str] = Auto,
    filename: str = "the_book_tm.pdf", ext: str = ".pdf",
    storage_path: str = "genericbooks/the_book_tm.pdf",
    cover_path: str = "/home/arthurpmrs/pdfshelf/covers/cover_1.jpg",
    active: bool = True, confirmed: bool = False, hash_id: str = Auto,
    book_id: int = Auto
) -> Book:

    if authors is Auto:
        authors = ["Plato", "Socrates"]
    if folder is Auto:
        folder = folder_factory()
    if tags is Auto:
        tags = ["Philosofy", "Mystic"]

    book = Book.from_raw_data({
        "title": title,
        "authors": authors,
        "year": year,
        "lang": lang,
        "publisher": publisher,
        "isbn13": isbn13,
        "parsed_isbn": parsed_isbn,
        "folder": folder,
        "filename": filename,
        "ext": ext,
        "storage_path": storage_path,
        "size": size,
        "tags": tags,
        "cover_path": cover_path,
        "book_id": None if book_id is Auto else book_id,
        "hash_id": None if hash_id is Auto else hash_id,
    })
    return book


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
    pkl_data = Path(rootdir) / "test_data" / "dummy_data.pkl"

    with open(pkl_data, 'rb') as inp:
        data = pickle.load(inp)
        books = data["books"]
        folders = data["folders"]

    for book in books:
        values = """NULL, :title, :authors, :year, :lang, :filename, :ext, 
                    :storage_path, :folder_id, :size, :tags, :added_date, 
                    :hash_id, :publisher, :isbn13, :parsed_isbn, :active, 
                    :confirmed, :cover_path"""
        cur.execute(f"INSERT INTO Book VALUES({values})", book)
        db_con.commit()

    for folder in folders:
        values = "NULL, :name, :path, :added_date, :active"
        cur.execute(f"INSERT INTO Folder VALUES({values})", folder)
        db_con.commit()


@pytest.fixture
def db_handler(db_con):
    return BookDBHandler(db_con)


@pytest.fixture
def folder_db_handler(db_con):
    return FolderDBHandler(db_con)


class TestBookDBHandlerInsert:

    @pytest.mark.usefixtures("setup_db")
    def test_insert_new_book_existing_folder(self, db_con, db_handler) -> None:
        book = book_factory(
            title="Automate the boring stuff with Python",
            authors=["Al Sweigart"],
            year=2015,
            publisher="No Starch Press",
            lang="en",
            isbn13="9781593275990",
            parsed_isbn="9781593275990",
            folder=folder_factory(
                name="Default",
                path=str(default_document_folder)
            ),
            size=78000,
            tags=[],
            filename="automate-the-boring-stuff.pdf",
            ext=".pdf",
            storage_path="pythonbooks/automate-the-boring-stuff.pdf",
        )
        book_id, folder_id = db_handler.insert_book(book)

        cur = db_con.cursor()
        book_count = cur.execute("SELECT count(*) from Book").fetchall()[0][0]
        folder_count = cur.execute(
            "SELECT count(*) from Folder").fetchall()[0][0]

        assert book_id == 14
        assert folder_id == 3
        assert book_count == 14
        assert folder_count == 3

    @pytest.mark.usefixtures("setup_db")
    def test_insert_existing_book_new_folder(self, db_con, db_handler) -> None:
        book = book_factory(
            title="Artificial Intelligence With Python",
            authors=["Prateek Joshi"],
            year=2017,
            publisher="No Starch Press",
            lang="en",
            isbn13="9781786464392",
            parsed_isbn="978-1-78646-439-2",
            folder=folder_factory(
                name="folder-3",
                path="/home/arthurpmrs/Documents/Library/dummie-data-source/folder-3"
            ),
            size=78000,
            tags=[],
            filename="Prateek Joshi-Artificial Intelligence with Python-Packt "
                     "Publishing - ebooks Account (2017).epub",
            ext=".epub",
            storage_path="pythonbooks/Prateek Joshi-Artificial Intelligence with"
                         " Python-Packt Publishing - ebooks Account (2017).epub",
        )
        book_id, folder_id = db_handler.insert_book(book)

        cur = db_con.cursor()
        book_count = cur.execute("SELECT count(*) from Book").fetchall()[0][0]
        folder_count = cur.execute(
            "SELECT count(*) from Folder").fetchall()[0][0]
        duplicate_count = cur.execute(
            "SELECT count(*) from Duplicate").fetchall()[0][0]

        assert book_id == 1
        assert folder_id == 4
        assert book_count == 13
        assert folder_count == 4
        assert duplicate_count == 1

    @pytest.mark.usefixtures("setup_db")
    def test_data_integrity_after_insert(self, db_handler) -> None:
        book = book_factory(
            title="Automate the boring stuff with Python",
            authors=["Al Sweigart"],
            year=2015,
            publisher="No Starch Press",
            lang="en",
            isbn13="9781593275990",
            parsed_isbn="9781593275990",
            folder=folder_factory(
                name="folder-3",
                path="/home/arthurpmrs/Documents/Library/dummie-data-source/folder-3"
            ),
            size=78000,
            tags=[],
            filename="automate-the-boring-stuff.pdf",
            ext=".pdf",
            storage_path="pythonbooks/automate-the-boring-stuff.pdf",
        )

        book_id, _ = db_handler.insert_book(book)
        loaded_book = db_handler.load_book_by_id(book_id)

        assert isinstance(loaded_book.authors, list) == True
        assert isinstance(loaded_book.tags, list) == True
        assert isinstance(loaded_book.added_date, datetime) == True
        assert isinstance(loaded_book.confirmed, bool) == True
        assert isinstance(loaded_book.active, bool) == True
        assert isinstance(loaded_book.size, float) == True
        assert isinstance(loaded_book.storage_path, Path) == True
        assert isinstance(loaded_book.folder, Folder) == True
        assert isinstance(loaded_book.folder.path,
                          Path) == True  # type: ignore
        assert isinstance(loaded_book.folder.active,
                          bool) == True  # type: ignore
        assert isinstance(loaded_book.folder.added_date,
                          datetime) == True  # type: ignore
        assert isinstance(loaded_book.cover_path, Path) == True  # type: ignore

    @pytest.mark.usefixtures("setup_db")
    def test_insert_none(self, db_handler) -> None:
        book = None
        with pytest.raises(TypeError):
            db_handler.insert_book(book)  # type: ignore

    @pytest.mark.usefixtures("setup_db")
    def test_duplicate_book_different_filename(self, db_con, db_handler) -> None:
        book = book_factory(
            title="Automate the boring stuff with Python",
            authors=["Al Sweigart"],
            year=2015,
            publisher="No Starch Press",
            lang="en",
            isbn13="9781593275990",
            parsed_isbn="9781593275990",
            folder=folder_factory(
                name="folder-3",
                path="/home/arthurpmrs/Documents/Library/dummie-data-source/folder-3"
            ),
            size=78000,
            tags=[],
            filename="automate-the-boring-stuff.pdf",
            ext=".pdf",
            storage_path="pythonbooks/automate-the-boring-stuff.pdf",
        )
        duplicate = book_factory(
            title="Automate the boring stuff with Python",
            authors=["Al Sweigart"],
            year=2015,
            publisher="No Starch Press",
            lang="en",
            isbn13="9781593275990",
            parsed_isbn="9781593275990",
            folder=folder_factory(
                name="folder-3",
                path="/home/arthurpmrs/Documents/Library/dummie-data-source/folder-3"
            ),
            size=78000,
            tags=[],
            filename="automate-the-boring-stuff-libgen.pdf",
            ext=".pdf",
            storage_path="pythonbooks/automate-the-boring-stuff-libgen.pdf",
        )
        book_id, folder_id = db_handler.insert_book(book)
        duplicate_book_id, duplicate_folder_id = db_handler.insert_book(
            duplicate)

        cur = db_con.cursor()
        book_count = cur.execute("SELECT count(*) from Book").fetchall()[0][0]
        folder_count = cur.execute(
            "SELECT count(*) from Folder").fetchall()[0][0]
        duplicate_count = (
            cur.execute("SELECT count(*) from Duplicate")
            .fetchall()[0][0]
        )

        assert book_id == duplicate_book_id
        assert folder_id == duplicate_folder_id
        assert book_count == 14
        assert folder_count == 4
        assert duplicate_count == 1

    @pytest.mark.usefixtures("setup_db")
    def test_insert_books(self, db_con, db_handler) -> None:
        books = [
            book_factory(
                title="Automate the boring stuff with Python",
                authors=["Al Sweigart"],
                year=2015,
                publisher="No Starch Press",
                lang="en",
                isbn13="9781593275990",
                parsed_isbn="9781593275990",
                folder=folder_factory(
                    name="folder-3",
                    path="/home/arthurpmrs/Documents/Library/dummie-data-source/folder-3"
                ),
                size=78000,
                tags=[],
                filename="automate-the-boring-stuff.pdf",
                ext=".pdf",
                storage_path="pythonbooks/automate-the-boring-stuff.pdf",
            ),
            book_factory(
                title="Python Crash Course",
                authors=["Eric Matthes"],
                year=2016,
                publisher="No Starch Press",
                lang="en",
                isbn13="9781593276034",
                parsed_isbn="9781593276034",
                folder=folder_factory(
                    name="folder-3",
                    path="/home/arthurpmrs/Documents/Library/dummie-data-source/folder-3"
                ),
                size=150000,
                tags=[],
                filename="python-crash-course.pdf",
                ext=".pdf",
                storage_path="pythonbooks/python-crash-course.pdf",
            ),
            book_factory(
                title="Artificial Intelligence With Python",
                authors=["Prateek Joshi"],
                year=2017,
                publisher="No Starch Press",
                lang="en",
                isbn13="9781786464392",
                parsed_isbn="978-1-78646-439-2",
                folder=folder_factory(
                    name="Default",
                    path=str(default_document_folder)
                ),
                size=78000,
                tags=[],
                filename="Prateek Joshi-Artificial Intelligence with Python-Packt Publishing - ebooks Account (2017).epub",
                ext=".epub",
                storage_path="pythonbooks/Prateek Joshi-Artificial Intelligence with Python-Packt Publishing - ebooks Account (2017).epub",
            ),
            book_factory(
                title="Fluent Python 2ed",
                authors=["Luciano Ramalho"],
                year=2022,
                publisher="O'Reilly Media",
                lang="en",
                isbn13="9781492056355",
                parsed_isbn="9781492056355",
                folder=folder_factory(
                    name="folder-4",
                    path="/home/arthurpmrs/Documents/Library/dummie-data-source/folder-4"
                ),
                size=78000,
                tags=[],
                filename="fluent-python-2.epub",
                ext=".epub",
                storage_path="pythonbooks/fluent-python-2.epub",
            )
        ]
        db_handler.insert_books(books)

        cur = db_con.cursor()
        book_count = cur.execute("SELECT count(*) from Book").fetchall()[0][0]
        folder_count = cur.execute(
            "SELECT count(*) from Folder").fetchall()[0][0]
        duplicate_count = (
            cur.execute("SELECT count(*) from Duplicate")
            .fetchall()[0][0]
        )

        assert book_count == 16
        assert folder_count == 5
        assert duplicate_count == 1

    @pytest.mark.usefixtures("setup_db")
    def test_insert_books_empty_list(self, db_con) -> None:
        handler = BookDBHandler(db_con)
        result = handler.insert_books([])
        assert result == None


class TestBookDBHandlerLoad:
    @pytest.mark.usefixtures("setup_db")
    def test_load_book_by_id(self, db_handler) -> None:
        book = db_handler.load_book_by_id(4)
        if book is not None:
            assert book.filename == "Ramalho_2021_Fluent Python_2nd.pdf"
            assert book.title == "Fluent Python"
            assert book.isbn13 == "9781491946008"

    @pytest.mark.usefixtures("setup_db")
    def test_load_book_by_id_id_not_found(self, db_handler) -> None:
        with pytest.raises(ValueError):
            db_handler.load_book_by_id(20)

    @pytest.mark.usefixtures("setup_db")
    def test_load_all_books(self, db_handler) -> None:
        books = db_handler.load_books()

        assert len(books) == 13

    @pytest.mark.usefixtures("setup_db")
    def test_load_sorting_by_title(self, db_handler) -> None:
        books = db_handler.load_books(sorting_key="title")

        assert books[0].book_id == 1
        assert books[0].title == "Artificial Intelligence With Python"
        assert books[9].book_id == 8
        assert books[9].title == "Programming Rust - Fast, Safe Systems Development"
        assert books[12].book_id == 12
        assert books[12].title == None

    @pytest.mark.usefixtures("setup_db")
    def test_load_sorting_by_added_date(self, db_handler) -> None:
        books = db_handler.load_books(sorting_key="added_date")

        assert books[0].book_id == 1
        assert books[12].book_id == 13

    @pytest.mark.usefixtures("setup_db")
    def test_load_sorting_by_year(self, db_handler) -> None:
        books = db_handler.load_books(sorting_key="year")

        assert books[0].book_id == 9
        assert books[0].year == 2009
        assert books[9].book_id == 8
        assert books[9].year == 2021
        assert books[12].book_id == 12
        assert books[12].year == None

    @pytest.mark.usefixtures("setup_db")
    def test_load_sorting_by_size(self, db_handler) -> None:
        books = db_handler.load_books(sorting_key="size")

        assert books[0].book_id == 2
        assert books[0].size == 1938322
        assert books[12].book_id == 1
        assert books[12].size == 51411688

    @pytest.mark.usefixtures("setup_db")
    def test_load_filtering_by_publisher(self, db_handler) -> None:
        books = db_handler.load_books(
            filter_key="publisher",
            filter_content="O'Reilly Media"
        )

        assert len(books) == 2
        assert books[0].hash_id == "1e6b5c65e04a42ab8cee0c9b17f1aa77"
        assert books[1].hash_id == "f8b0da97fe22bc5f58e4a71a19b12096"

    @pytest.mark.usefixtures("setup_db")
    def test_load_filtering_by_ext(self, db_handler) -> None:
        books = db_handler.load_books(
            filter_key="ext",
            filter_content=".pdf"
        )

        assert len(books) == 8
        assert books[0].hash_id == "1e6b5c65e04a42ab8cee0c9b17f1aa77"
        assert books[1].hash_id == "666a2b474f223232c8ddc7cdde01678a"
        assert books[-1].hash_id == "1ec74ef4f392fea4987aa57a168a351a"

    @pytest.mark.usefixtures("setup_db")
    def test_load_filtering_by_year(self, db_handler) -> None:
        books = db_handler.load_books(
            filter_key="year",
            filter_content=2020
        )

        assert len(books) == 2
        assert books[0].hash_id == "1e6b5c65e04a42ab8cee0c9b17f1aa77"
        assert books[-1].hash_id == "1ec74ef4f392fea4987aa57a168a351a"

    @pytest.mark.usefixtures("setup_db")
    def test_load_filtering_by_tag(self, db_handler) -> None:
        books = db_handler.load_books(
            filter_key="tag",
            filter_content="python"
        )

        assert len(books) == 7
        assert books[0].hash_id == "48e296cc59417f8f9dcfe5676a544952"
        assert books[3].hash_id == "666a2b474f223232c8ddc7cdde01678a"
        assert books[-1].hash_id == "f81cb933ed6afa10c437bae3709c3194"

    @pytest.mark.usefixtures("setup_db")
    def test_load_filtering_by_active(self, db_handler) -> None:
        books = db_handler.load_books(
            filter_key="active",
            filter_content=1
        )

        assert len(books) == 9
        assert books[2].hash_id == "1e6b5c65e04a42ab8cee0c9b17f1aa77"
        assert books[5].hash_id == "f8b0da97fe22bc5f58e4a71a19b12096"
        assert books[-1].hash_id == "efe8e540e2e6175aad863264040c71a1"

    @pytest.mark.usefixtures("setup_db")
    def test_load_filtering_by_confirmed(self, db_handler) -> None:
        books = db_handler.load_books(
            filter_key="confirmed",
            filter_content=1
        )

        assert len(books) == 4
        assert books[1].hash_id == "f8b0da97fe22bc5f58e4a71a19b12096"
        assert books[-1].hash_id == "efe8e540e2e6175aad863264040c71a1"

    @pytest.mark.usefixtures("setup_db")
    def test_load_filtering_by_author(self, db_handler) -> None:
        books = db_handler.load_books(
            filter_key="author",
            filter_content="Luciano"
        )

        assert len(books) == 1
        assert books[0].hash_id == "666a2b474f223232c8ddc7cdde01678a"

    @pytest.mark.usefixtures("setup_db")
    def test_load_no_filter_match(self, db_handler) -> None:
        books = db_handler.load_books(
            filter_key="author",
            filter_content="Rasputcha"
        )

        assert isinstance(books, list)
        assert len(books) == 0

    @pytest.mark.usefixtures("setup_db")
    def test_load_filtering_and_sorting(self, db_handler) -> None:
        books = db_handler.load_books(
            filter_key="tag",
            filter_content="python",
            sorting_key="year"
        )

        assert len(books) == 7
        assert books[0].hash_id == "666a2b474f223232c8ddc7cdde01678a"
        assert books[4].hash_id == "f81cb933ed6afa10c437bae3709c3194"
        assert books[-1].hash_id == "8fbfb690a5ceba47633bb7ab77000d5d"


class TestBookDBHandlerUpdate:

    @pytest.mark.usefixtures("setup_db")
    def test_update_single_property(self, db_handler) -> None:
        content_1 = {"authors": '["Prateek Joshi", "John Cena"]'}
        db_handler.update_book(book_id=1, content=content_1)
        book_1 = db_handler.load_book_by_id(book_id=1)

        assert len(book_1.authors) == 2

        content_2 = {"title": "Fluent Python 2nd"}
        db_handler.update_book(book_id=4, content=content_2)
        book_2 = db_handler.load_book_by_id(book_id=4)

        assert book_2.title == "Fluent Python 2nd"

        content_3 = {"tags": '["Python"]'}
        db_handler.update_book(book_id=7, content=content_3)
        book_3 = db_handler.load_book_by_id(book_id=7)

        assert len(book_3.tags) == 1

        content_4 = {"publisher": "Packt"}
        db_handler.update_book(book_id=5, content=content_4)
        book_4 = db_handler.load_book_by_id(book_id=5)

        assert book_4.publisher == "Packt"

        content_5 = {"year": 2021}
        db_handler.update_book(book_id=13, content=content_5)
        book_5 = db_handler.load_book_by_id(book_id=13)

        assert book_5.year == 2021

        content_6 = {"lang": "ptBR"}
        db_handler.update_book(book_id=4, content=content_6)
        book_6 = db_handler.load_book_by_id(book_id=4)
        assert book_6.lang == "ptBR"

    @pytest.mark.usefixtures("setup_db")
    def test_update_multiple_properties(self, db_handler) -> None:
        book_1 = db_handler.load_book_by_id(book_id=1)
        content_1 = {
            "authors": '["Prateek Joshi", "John Cena"]',
            "title": "AI with Python",
            "year": 2021,
        }
        db_handler.update_book(book_id=1, content=content_1)
        book_1.authors = json.loads(content_1["authors"])
        book_1.title = content_1["title"]
        book_1.year = content_1["year"]
        book_1_after = db_handler.load_book_by_id(book_id=1)

        assert book_1 == book_1_after

        book_2 = db_handler.load_book_by_id(book_id=8)
        content_2 = {
            "tags": '["Rust"]',
            "title": "Coding Rust blah",
            "lang": "jp",
            "authors": '["Jim", "Potter", "Nanakuza"]'
        }
        db_handler.update_book(book_id=8, content=content_2)
        book_2.authors = json.loads(content_2["authors"])
        book_2.tags = json.loads(content_2["tags"])
        book_2.lang = content_2["lang"]
        book_2.title = content_2["title"]
        book_2_after = db_handler.load_book_by_id(book_id=8)

        assert book_2 == book_2_after

    @pytest.mark.usefixtures("setup_db")
    def test_update_empty_dict(self, db_handler) -> None:
        assert db_handler.update_book(book_id=1, content={}) == False

    @pytest.mark.usefixtures("setup_db")
    def test_update_invalid_key(self, db_handler) -> None:
        content = {
            "geezers": 52
        }
        assert db_handler.update_book(book_id=1, content=content) == False

    @pytest.mark.usefixtures("setup_db")
    def test_update_only_protected_fields(self, db_handler) -> None:
        content_1 = {
            "size": 1500,
            "added_date": "2020-12-30",
            "hash_id": "bla"
        }

        content_2 = {
            "isbn13": "bla",
            "parsed_isbn": "bla",
            "active": 0,
            "confirmed": 1,
        }

        content_3 = {
            "folder_id": 4,
            "filename": "bla.mp3",
            "storage_path": "bla/bla",
            "ext": ".mp3"
        }

        with pytest.raises(ValueError):
            db_handler.update_book(book_id=1, content=content_1)

        with pytest.raises(ValueError):
            db_handler.update_book(book_id=4, content=content_2)

        with pytest.raises(ValueError):
            db_handler.update_book(book_id=8, content=content_3)

    @pytest.mark.usefixtures("setup_db")
    def test_update_protected_fields(self, db_handler) -> None:
        content = {
            "authors": '["Prateek Joshi", "John Cena"]',
            "title": "AI with Python",
            "year": 2021,
            "filename": "AI_with_python.pdf"
        }
        with pytest.raises(ValueError):
            db_handler.update_book(book_id=1, content=content)

    @pytest.mark.usefixtures("setup_db")
    def test_update_null_field(self, db_handler) -> None:
        content = {
            "title": "NumPy Cookbook",
            "authors": '["Ivan Idris"]',
            "year": 2015,
            "publisher": "Packt"
        }
        res = db_handler.update_book(book_id=6, content=content)
        book = db_handler.load_book_by_id(book_id=6)

        assert book.title == content["title"]
        assert book.authors == json.loads(content["authors"])
        assert book.year == content["year"]
        assert book.publisher == content["publisher"]
        assert res == True


class TestBookDBHandlerDelete:

    @pytest.mark.usefixtures("setup_db")
    def test_delete_single_row(self, db_con, db_handler) -> None:
        cur = db_con.cursor()
        db_handler.delete_book(book_id=13)
        count = (
            cur.execute("SELECT count(*) from Book")
            .fetchall()[0][0]
        )
        assert count == 12

    @pytest.mark.usefixtures("setup_db")
    def test_delete_two_row(self, db_con, db_handler) -> None:
        cur = db_con.cursor()
        db_handler.delete_book(book_id=1)
        db_handler.delete_book(book_id=2)

        count = (
            cur.execute("SELECT count(*) from Book")
            .fetchall()[0][0]
        )

        assert count == 11


class TestFolderDBHandlerInsert:

    @pytest.mark.usefixtures("setup_db")
    def test_insert_folder(self, folder_db_handler) -> None:
        folder = folder_factory()
        folder_id = folder_db_handler.insert_folder(folder)
        folder.folder_id = folder_id

        folders = folder_db_handler.load_folders()
        folder_loaded = folder_db_handler.load_folder_by_id(folder_id)

        assert len(folders) == 4
        assert folder_loaded == folder

    @pytest.mark.usefixtures("setup_db")
    def test_insert_existing_folder(self, folder_db_handler) -> None:
        folder = folder_factory(
            name="folder-0",
            path="/home/arthurpmrs/Documents/Library/dummie-data-source/folder-0"
        )
        folder_id = folder_db_handler.insert_folder(folder)
        assert folder_id == 1

    @pytest.mark.usefixtures("setup_db")
    def test_insert_none_folder(self, folder_db_handler) -> None:
        with pytest.raises(TypeError):
            folder_id = folder_db_handler.insert_folder(None)


class TestFolderDBHandlerLoad:

    @pytest.mark.usefixtures("setup_db")
    def test_load_folder_by_id(self, folder_db_handler) -> None:
        folder = folder_db_handler.load_folder_by_id(folder_id=2)

        assert folder.folder_id == 2
        assert folder.name == "folder-1"
        assert folder.path == Path(
            "/home/arthurpmrs/Documents/Library/dummie-data-source/folder-1"
        )
        assert folder.active == False
        assert isinstance(folder.folder_id, int)
        assert isinstance(folder.added_date, datetime)
        assert isinstance(folder.active, bool)
        assert isinstance(folder.name, str)
        assert isinstance(folder.path, Path)

    @pytest.mark.usefixtures("setup_db")
    def test_load_all_folders(self, folder_db_handler) -> None:
        folders = folder_db_handler.load_folders()

        assert len(folders) == 3
        assert folders[0].path == Path(
            "/home/arthurpmrs/Documents/Library/dummie-data-source/folder-0"
        )
        assert folders[1].name == "folder-1"
        assert folders[2].name == "Default"

    @pytest.mark.usefixtures("setup_db")
    def test_load_order_by_name(self, folder_db_handler) -> None:
        folders = folder_db_handler.load_folders(sorting_key="name")

        assert folders[0].folder_id == 3
        assert folders[1].folder_id == 1
        assert folders[2].folder_id == 2

    @pytest.mark.usefixtures("setup_db")
    def test_load_order_by_date(self, folder_db_handler) -> None:
        folders = folder_db_handler.load_folders(sorting_key="date")

        assert folders[0].folder_id == 1
        assert folders[1].folder_id == 2
        assert folders[2].folder_id == 3

    @pytest.mark.usefixtures("setup_db")
    def test_load_order_by_path(self, folder_db_handler) -> None:
        folders = folder_db_handler.load_folders(sorting_key="path")

        assert folders[0].folder_id == 1
        assert folders[1].folder_id == 2
        assert folders[2].folder_id == 3

    @pytest.mark.usefixtures("setup_db")
    def test_load_filter_by_active(self, folder_db_handler) -> None:
        folders = folder_db_handler.load_folders(filter_key="active")

        assert len(folders) == 2
        assert folders[0].folder_id == 1
        assert folders[1].folder_id == 3

    @pytest.mark.usefixtures("setup_db")
    def test_load_filter_by_not_active(self, folder_db_handler) -> None:
        folders = folder_db_handler.load_folders(filter_key="not_active")

        assert len(folders) == 1
        assert folders[0].folder_id == 2


class TestFolderDBHandlerUpdate:
    @pytest.mark.usefixtures("setup_db")
    def test_update_one_field(self, folder_db_handler) -> None:
        folder_id = 2
        content = {
            "name": "folder-0X"
        }
        success = folder_db_handler.update_folder(folder_id, content)
        folder = folder_db_handler.load_folder_by_id(folder_id)

        assert success == True
        assert folder.name == content["name"]

    @pytest.mark.usefixtures("setup_db")
    def test_update_many_field(self, folder_db_handler) -> None:
        folder_id = 1
        content = {
            "name": "folder-0X",
            "path": "/home/arthurpmrs/books/dummie-data-source/folder-1"
        }
        success = folder_db_handler.update_folder(folder_id, content)
        folder = folder_db_handler.load_folder_by_id(folder_id)

        assert success == True
        assert folder.name == content["name"]
        assert folder.path == Path(content["path"])

    @pytest.mark.usefixtures("setup_db")
    def test_update_empty_dict(self, folder_db_handler) -> None:
        assert folder_db_handler.update_folder(folder_id=2,
                                               content={}) == False

    @pytest.mark.usefixtures("setup_db")
    def test_update_invalid_field(self, folder_db_handler) -> None:
        content = {
            "geezers": 52
        }
        assert folder_db_handler.update_folder(folder_id=2,
                                               content=content) == False

    @pytest.mark.usefixtures("setup_db")
    def test_update_protected_field(self, folder_db_handler) -> None:
        with pytest.raises(ValueError):
            folder_db_handler.update_folder(folder_id=1,
                                            content={"active": 0})
        with pytest.raises(ValueError):
            folder_db_handler.update_folder(folder_id=2,
                                            content={"added_date": "2020-08-01"})
        with pytest.raises(ValueError):
            folder_db_handler.update_folder(folder_id=3,
                                            content={"folder_id": 5})


class TestFolderDBHandlerDelete:
    @pytest.mark.usefixtures("setup_db")
    def test_delete_single_row(self, db_con, folder_db_handler) -> None:
        success = folder_db_handler.delete_folder(folder_id=2)

        cur = db_con.cursor()
        folder_count = (
            cur.execute("SELECT count(*) from Folder")
            .fetchall()[0][0]
        )
        book_count = (
            cur.execute("SELECT count(*) from Book")
            .fetchall()[0][0]
        )

        assert success == True
        assert folder_count == 2
        assert book_count == 6

    @pytest.mark.usefixtures("setup_db")
    def test_delete_two_row(self, db_con, folder_db_handler) -> None:
        success_1 = folder_db_handler.delete_folder(folder_id=1)
        success_2 = folder_db_handler.delete_folder(folder_id=3)

        cur = db_con.cursor()
        folder_count = (
            cur.execute("SELECT count(*) from Folder")
            .fetchall()[0][0]
        )
        book_count = (
            cur.execute("SELECT count(*) from Book")
            .fetchall()[0][0]
        )

        assert success_1 == True
        assert success_2 == True
        assert book_count == 7
        assert folder_count == 1
