import logging
from pathlib import Path
from pdfshelf.domain import Book
from pdfshelf.fetchmetadata import MetadataFetcher
from pdfshelf.config import config_folder

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    f_format = logging.Formatter('%(asctime)s %(name)-22s %(levelname)-8s [%(lineno)-3s] %(message)s', "%Y-%m-%d %H:%M")
    s_format = logging.Formatter('%(name)-22s %(levelname)-8s [%(lineno)-3s] %(message)s')

    f_handler = logging.FileHandler(config_folder / "pdfshelf_dependencies.log")
    f_handler.setLevel(logging.DEBUG)
    f_handler.setFormatter(f_format)

    s_handler = logging.StreamHandler()
    s_handler.setLevel(logging.WARNING)
    s_handler.setFormatter(s_format)

    logger.addHandler(f_handler)
    logger.addHandler(s_handler)

    logging.getLogger("pdfshelf").propagate = False

def main1():
    folder = {
        "name": "foldinha",
        "path": "/home/Documents/Library/Livros"
    }

    book = Book(
        title="Modeling and simulation in Python",
        authors=["Jason M. Kinser"],
        year=2022,
        lang="en",
        filename="Jason M. Kinser - Modeling and Simulation in Python-Chapman & Hall (2022).pdf",
        ext="pdf",
        storage_path="teste/Jason M. Kinser - Modeling and Simulation in Python-Chapman & Hall (2022).pdf",
        folder=folder,
        size=100000,
        publisher="CRC Press",
        isbn13="978-1-032-11648-8"
    )

    print(book)
    print(book.folder)

def main2():
    path = Path("/home/arthurpmrs/Documents/Library/Nova pasta/William Shotts - The Linux Command Line_ A Complete Introduction-No Starch Press (2019).pdf")
    fetcher = MetadataFetcher()
    book = fetcher.fetch_metadata_from_file(path)
    print(book)
    print(book.folder)

def main3():
    folderpath = Path("/home/arthurpmrs/Downloads/test_data/selected")
    fetcher = MetadataFetcher()
    books, success_count = fetcher.get_books_from_folder(folderpath)
    print(f"Metadata successful fetching: {success_count}")
    for book, success in books:
        print(success)
        print(book)
        print(" ")

def get_epub():
    folderpath = Path("/home/arthurpmrs/Documents/Library/epubs")
    fetcher = MetadataFetcher()
    books, success_count  = fetcher.get_books_from_folder(folderpath)
    print(f"Metadata successful fetching: {success_count}")
    for book, success in books:
        print(success)
        print(book)
        print(" ")


if __name__ == "__main__":
    setup_logging()
    main3()