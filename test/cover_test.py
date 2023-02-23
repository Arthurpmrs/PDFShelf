import os
import pytest
from pathlib import Path
from pdfshelf.cover import FileCoverExtractor, OLCoverFetcher, BookCover
from pdfshelf.importer import book_from_file, books_from_folder
from pdfshelf.config import COVER_FOLDER
from pdfshelf.utilities import book_factory, folder_factory
# TODO: Tests que não dependem de pdfshelf.importer


@pytest.fixture
def rootdir():
    return os.path.dirname(os.path.abspath(__file__))


class TestFileCoverExtractor:

    def test_extract_from_pdf(self, tmp_path):
        filename = "Amol M. Jagtap, Ajit S. Mali - Data Structures using C_ A Practical Approach for Beginners-Chapman and Hall_CRC (2021).pdf"
        path = Path("/home/arthurpmrs/books") / filename

        book = book_from_file(path)

        fake_cover_folder = tmp_path / "cover"
        fake_cover_folder.mkdir()

        cover_extractor = FileCoverExtractor(fake_cover_folder)
        extract_func = cover_extractor.get_format_parser(book.ext)

        book = extract_func(book)
        expected_cover_path = COVER_FOLDER / f"cover_{book.hash_id}.jpg"
        assert expected_cover_path.exists() == True


class TestCoverFetcher:
    def test_fething(self):
        folder_path = Path("/home/arthurpmrs/books")
        books = books_from_folder(folder_path)

        fetcher = OLCoverFetcher()
        books = fetcher.fetch(books)
        for book in books:
            print(book.hash_id, book.cover_path)

        for filename in folder_path.iterdir():
            print("FS-> ", filename)

    def test_fetch_one_book_cover(self):
        filename = "Amol M. Jagtap, Ajit S. Mali - Data Structures using C_ A Practical Approach for Beginners-Chapman and Hall_CRC (2021).pdf"
        path = Path("/home/arthurpmrs/books") / filename
        book = book_from_file(path)
        print(book.isbn13)
        books = [book]
        fetcher = OLCoverFetcher()
        books = fetcher.fetch(books)
        for book in books:
            print(book.hash_id, book.cover_path)


class TestBookCover:
    # def test_get_cover_for_book(self) -> None:
    #     filename = "Amol M. Jagtap, Ajit S. Mali - Data Structures using C_ A Practical Approach for Beginners-Chapman and Hall_CRC (2021).pdf"
    #     folderpath = "/home/arthurpmrs/books"
    #     isbn13 = "9780367616311"
    #     fetcher = OLCoverFetcher()
    #     extractor = FileCoverExtractor()
    #     folder = folder_factory(path=folderpath)
    #     book = book_factory(isbn13=isbn13, filename=filename, folder=folder,
    #                         storage_path=filename)
    #     book.cover_path = None
    #     print(book)
    #     bookcover = BookCover(fetcher, extractor)
    #     book = bookcover.get_cover_for_book(book)
    #     assert book.cover_path is not None

    # def test_get_cover_for_corrupted_book(self, rootdir) -> None:
    #     filename = "corrupted.pdf"
    #     storage_path = f'test_data/{filename}'
    #     test_file = os.path.join(rootdir, storage_path)
    #     isbn13 = "978036311"
    #     fetcher = OLCoverFetcher()
    #     extractor = FileCoverExtractor()
    #     folder = folder_factory(path=rootdir)
    #     book = book_factory(isbn13=isbn13, filename=filename, folder=folder,
    #                         storage_path=storage_path)
    #     book.cover_path = None
    #     print(book)
    #     bookcover = BookCover(fetcher, extractor)
    #     book = bookcover.get_cover_for_book(book)
    #     assert book.cover_path is None

    def test_get_cover_for_books(self) -> None:
        folder_path = Path("/home/arthurpmrs/books")
        books = books_from_folder(folder_path)

        fetcher = OLCoverFetcher()
        extractor = FileCoverExtractor()
        bookcover = BookCover(fetcher, extractor)
        books = bookcover.get_cover_for_books(books)

        for book in books:
            print(book.hash_id, book.cover_path)

        for filename in folder_path.iterdir():
            print("FS-> ", filename)
