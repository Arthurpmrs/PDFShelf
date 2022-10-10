import csv
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from pdfshelf.domain import Book
from pdfshelf.fetchmetadata import MetadataFetcher
from pdfshelf.config import config_folder

from pdfshelf.database import DatabaseConnector
def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    f_format = logging.Formatter('%(asctime)s %(name)-22s %(levelname)-8s [%(lineno)-3s] %(message)s', "%Y-%m-%d %H:%M")
    s_format = logging.Formatter('%(name)-22s %(levelname)-8s [%(lineno)-3s] %(message)s')

    f_handler = RotatingFileHandler(config_folder / "pdfshelf_dependencies.log", maxBytes=2500000, backupCount=25)
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
    folderpath = Path("/home/arthurpmrs/Downloads/epubs/selected")
    fetcher = MetadataFetcher()
    books, success_count  = fetcher.get_books_from_folder(folderpath)
    print(f"Metadata successful fetching: {success_count}")
    for book, success in books:
        print(book)

def prototype_db():
    with DatabaseConnector() as con:
        print("foi")

def create_dummie_csv_data():
    folderpaths =[
        Path("/home/arthurpmrs/Documents/Library/dummie-data-source/folder-0"),
        Path("/home/arthurpmrs/Documents/Library/dummie-data-source/folder-1")
    ]
    individuals = [
        Path("/home/arthurpmrs/Documents/Library/dummie-data-source/individuals/Lehman_2017_Mathematics for Computer Science.pdf"),
        Path("/home/arthurpmrs/Documents/Library/dummie-data-source/individuals/Vince_2020_Foundation mathematics for computer science_A visual approach.pdf")
    ] 

    fetcher = MetadataFetcher()

    books = []
    folders = []

    for folderpath in folderpaths:
        bks, success_count = fetcher.get_books_from_folder(folderpath)
        for (book, success) in bks:
            parsed_book, parsed_folder = book.get_parsed_dict()
            if not parsed_folder in folders:
                folders.append(parsed_folder)

            parsed_book.update({"folder_id": 1 + folders.index(parsed_folder)}) 
            books.append(parsed_book)
    
    for ind in individuals:
        book, success = fetcher.get_book_from_file(ind)
        parsed_book, parsed_folder = book.get_parsed_dict()
        if not parsed_folder in folders:
            folders.append(parsed_folder)

        parsed_book.update({"folder_id": 1 + folders.index(parsed_folder)}) 
        books.append(parsed_book)

    book_headers = list(parsed_book.keys())
    folder_headers = list(parsed_folder.keys())

    with open('dummie_book_data.csv', 'w') as csvfile_book:
        writer = csv.DictWriter(csvfile_book, fieldnames=book_headers)
        writer.writeheader()
        writer.writerows(books)
    
    with open('dummie_folder_data.csv', 'w') as csvfile_folders:
        writer = csv.DictWriter(csvfile_folders, fieldnames=folder_headers)
        writer.writeheader()
        writer.writerows(folders)


if __name__ == "__main__":
    create_dummie_csv_data()