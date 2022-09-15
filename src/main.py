from pathlib import Path
from pdfshelf.domain import Book
from pdfshelf.fetchmetadata import MetadataFetcher
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
    folderpath = Path("/home/arthurpmrs/Documents/Library/Livros")
    fetcher = MetadataFetcher()
    books, success_count = fetcher.fetch_metadata_from_folder(folderpath)
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
    get_epub()
