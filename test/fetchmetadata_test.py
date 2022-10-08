import os
import pytest
import logging
from pathlib import Path
from isbnlib import ISBNLibException
from pdfshelf.fetchmetadata import MetadataFetcher
from pdfshelf.exceptions import FormatNotSupportedError

@pytest.fixture
def rootdir():
    return os.path.dirname(os.path.abspath(__file__))

class TestMetadataFetcher:

    fetch = MetadataFetcher()

    def test_get_books_from_folder_no_folder(self, tmp_path) -> None:
        not_created_dir = tmp_path / "folder1"

        with pytest.raises(FileNotFoundError):
            self.fetch.get_books_from_folder(not_created_dir)

    def test_get_books_from_folder_empty_folder(self, tmp_path) -> None:
        tmp_dir = tmp_path / "folder"
        tmp_dir.mkdir()

        assert self.fetch.get_books_from_folder(tmp_dir) == ([], 0)

    def test_get_book_from_file_does_not_exist(self, tmp_path) -> None:
        non_existing_pdf = tmp_path / "folder" / "file.pdf"
        non_existing_epub = tmp_path / "folder" / "file.epub"

        with pytest.raises(FileNotFoundError):
            self.fetch.get_book_from_file(non_existing_pdf)
            self.fetch.get_book_from_file(non_existing_epub)

    ## Test pdf and epub with None metadata from isbnlib
    
    def test_get_book_from_file_not_supported_extenstion(self, tmp_path) -> None:
        tmp_folder = tmp_path / "test_folder"
        tmp_folder.mkdir()

        tmp_file = tmp_folder / "file.txt"
        tmp_file.write_text("hello_world")

        with pytest.raises(FormatNotSupportedError):
            self.fetch.get_book_from_file(tmp_file)
    
    def test_get_book_from_file_pdf_has_isbn13(self, rootdir, mocker) -> None:
        test_file = os.path.join(rootdir, 'test_data/how_to_code_in_python_isbn13.pdf')
        
        mocker.patch(
            "pdfshelf.fetchmetadata.isbnlib.meta",
            return_value={
                "Title": "Mocking a PDF",
                "Authors": ["Mockerson Mock", "Mockiney Mockares"],
                "Year": 2012,
                "Publisher": "John Mock and Sons",
                "Language": "en",
                "ISBN-13": "9780999773017"
            }
        )

        book, success = self.fetch.get_book_from_file(Path(test_file))

        assert success == True
        assert book.parsed_isbn == "978-0-9997730-1-7"
        assert book.isbn10 == None
        assert book.isbn13 == "9780999773017"
        assert book.ext == ".pdf"

    def test_get_book_from_file_pdf_has_isbn10(self, rootdir, mocker) -> None:
        test_file = os.path.join(rootdir, 'test_data/php5_isbn10.pdf')
        
        mocker.patch(
            "pdfshelf.fetchmetadata.isbnlib.meta",
            return_value={
                "Title": "Mocking a PDF",
                "Authors": ["Mockerson Mock", "Mockiney Mockares"],
                "Year": 2012,
                "Publisher": "John Mock and Sons",
                "Language": "en",
                "ISBN-13": "9780131471498"
            }
        )

        book, success = self.fetch.get_book_from_file(Path(test_file))
        
        assert success == True
        assert book.parsed_isbn == "0-131-47149-X"
        assert book.isbn13 == "9780131471498"
        assert book.isbn10 == None
        assert book.ext == ".pdf"

    def test_get_book_from_file_pdf_no_valid_isbn(self, rootdir, mocker) -> None:
        test_file = os.path.join(rootdir, 'test_data/think_python_2_no_isbn.pdf')

        book, success = self.fetch.get_book_from_file(Path(test_file))
        
        assert success == False
        assert book.parsed_isbn == None
        assert book.isbn13 == None
        assert book.isbn10 == None
        assert book.ext == ".pdf"

    def test_get_book_from_file_epub_has_isbn13(self, rootdir, mocker) -> None:
        test_file = os.path.join(rootdir, 'test_data/craft-isbn-13.epub')
        
        mocker.patch(
            "pdfshelf.fetchmetadata.isbnlib.meta",
            return_value={
                "Title": "Mocking a EPUB",
                "Authors": ["Mockerson Mock", "Mockiney Mockares"],
                "Year": 2012,
                "Publisher": "John Mock and Sons",
                "Language": "en",
                "ISBN-13": "9781411682979"
            }
        )

        book, success = self.fetch.get_book_from_file(Path(test_file))

        assert success == True
        assert book.parsed_isbn == "978-1-4116-8297-9"
        assert book.isbn10 == None
        assert book.isbn13 == "9781411682979"
        assert book.ext == ".epub"

    def test_get_book_from_file_epub_has_isbn10(self, rootdir, mocker) -> None:
        test_file = os.path.join(rootdir, 'test_data/git-magic-isbn-10.epub')
        
        mocker.patch(
            "pdfshelf.fetchmetadata.isbnlib.meta",
            return_value={
                "Title": "Mocking a EPUB",
                "Authors": ["Mockerson Mock", "Mockiney Mockares"],
                "Year": 2012,
                "Publisher": "John Mock and Sons",
                "Language": "en",
                "ISBN-13": "9781451523348"
            }
        )

        book, success = self.fetch.get_book_from_file(Path(test_file))
        
        assert success == True
        assert book.parsed_isbn == "1451523343"
        assert book.isbn13 == "9781451523348"
        assert book.isbn10 == None
        assert book.ext == ".epub"

    def test_get_book_from_file_epub_no_valid_isbn(self, rootdir, mocker) -> None:
        test_file = os.path.join(rootdir, 'test_data/beginners-in-open-source-no-isbn.epub')

        book, success = self.fetch.get_book_from_file(Path(test_file))
        
        assert success == False
        assert book.parsed_isbn == None
        assert book.isbn13 == None
        assert book.isbn10 == None
        assert book.ext == ".epub"

    def test_get_book_from_file_corrupted_pdf(self, rootdir) -> None:
        test_file = os.path.join(rootdir, 'test_data/corrupted.pdf')

        book, success = self.fetch.get_book_from_file(Path(test_file))
        
        assert success == False
        assert book.parsed_isbn == None
        assert book.isbn13 == None
        assert book.isbn10 == None

    def test_get_book_from_file_corrupted_epub(self, rootdir) -> None:
        test_file = os.path.join(rootdir, 'test_data/corrupted.epub')

        book, success = self.fetch.get_book_from_file(Path(test_file))
        
        assert success == False
        assert book.parsed_isbn == None
        assert book.isbn13 == None
        assert book.isbn10 == None

    def test_get_book_from_file_api_failed(self, rootdir, mocker) -> None:
        test_file = os.path.join(rootdir, 'test_data/how_to_code_in_python_isbn13.pdf')

        mocker.patch(
            "pdfshelf.fetchmetadata.isbnlib.meta",
            side_effect=ISBNLibException("ISBN API Failed!")
        )

        book, success = self.fetch.get_book_from_file(Path(test_file))

        assert success == False
        assert book.title == ""
        assert book.year == 0
        assert book.isbn10 == None
        assert book.isbn13 == None
        assert book.parsed_isbn == None

