import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from pdfshelf.importer import books_from_folder
from pdfshelf.config import config_folder
from pdfshelf.database import DatabaseConnector, BookDBHandler


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    f_format = logging.Formatter(
        '%(asctime)s %(name)-22s %(levelname)-8s [%(lineno)-3s] %(message)s', "%Y-%m-%d %H:%M")
    s_format = logging.Formatter(
        '%(name)-22s %(levelname)-8s [%(lineno)-3s] %(message)s')

    f_handler = RotatingFileHandler(
        config_folder / "pdfshelf_dependencies.log", maxBytes=2500000, backupCount=25)
    f_handler.setLevel(logging.DEBUG)
    f_handler.setFormatter(f_format)

    s_handler = logging.StreamHandler()
    s_handler.setLevel(logging.WARNING)
    s_handler.setFormatter(s_format)

    logger.addHandler(f_handler)
    logger.addHandler(s_handler)

    logging.getLogger("pdfshelf").propagate = False


def insert1():
    path = Path("/home/arthurpmrs/Documents/new_books")

    fetcher = MetadataFetcher()
    books, total_success_count = fetcher.get_books_from_folder(path)
    cleaned_books = []
    print(f"Successes: {total_success_count}")
    for book, success in books:
        print(f"{success} | {book}")
        cleaned_books.append(book)

    with DatabaseConnector() as con:
        handler = BookDBHandler(con)
        handler.insert_books(cleaned_books)


def update1():
    with DatabaseConnector() as con:
        handler = BookDBHandler(con)
        content = {
            "title": "Matemática discreta e suas aplicações",
            "lang": "ptbr",
            "authors": '["Kenneth H. Rosen"]',
            "year": 2009,
            "publisher": "McGraw-Hill",
        }
        handler.update_book(book_id=3, content=content)


def delete1():
    with DatabaseConnector() as con:
        handler = BookDBHandler(con)
        handler.delete_book(book_id=5)


def load1():
    with DatabaseConnector() as con:
        handler = BookDBHandler(con)

        books = handler.load_books()

        for book in books:
            print(book.book_id, book.title, book.authors)


def test_import():
    path = Path(r"/home/arthurpmrs/Documents/new_books")
    books = books_from_folder(path)
    for book in books:
        print(book)


if __name__ == "__main__":
    test_import()
