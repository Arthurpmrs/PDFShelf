import os
import pytest
import logging
from pdfshelf.fetchmetadata import MetadataFetcher

@pytest.fixture
def rootdir():
    return os.path.dirname(os.path.abspath(__file__))

class TestMetadataFetcher:

    logging.disable(logging.CRITICAL)
    fetch = MetadataFetcher()

    def test_get_books_from_folder_no_directory(self, tmp_path) -> None:
        not_created_dir = tmp_path / "folder1"

        with pytest.raises(FileNotFoundError):
            self.fetch.get_books_from_folder(not_created_dir)


    def test_get_book_from_file_no_file(self, tmp_path) -> None:
        non_existing_file = tmp_path / "folder1.pdf"

        with pytest.raises(FileNotFoundError):
            self.fetch.get_book_from_file(non_existing_file)

    def test_get_isbn_from_pdf_no_isbn(self, rootdir) -> None:
        test_file = os.path.join(rootdir, 'test_data/think_python_2_no_isbn.pdf')

        isbn10, isbn13 = self.fetch._get_isbn_from_pdf(test_file)

        assert isbn10 == ""
        assert isbn13 == ""

    def test_get_isbn_from_pdf_isbn10(self, rootdir) -> None:
        test_file = os.path.join(rootdir, 'test_data/php5_isbn10.pdf')

        isbn10, isbn13 = self.fetch._get_isbn_from_pdf(test_file)

        assert isbn10 == "0-131-47149-X"
        assert isbn13 == ""

    def test_get_isbn_from_pdf_isbn13(self, rootdir) -> None:
        test_file = os.path.join(rootdir, 'test_data/how_to_code_in_python_isbn13.pdf')

        isbn10, isbn13 = self.fetch._get_isbn_from_pdf(test_file)

        assert isbn10 == ""
        assert isbn13 == "978-0-9997730-1-7"    

    ## Testar _fetch_metadata method
    ## Testar _get_isbn_from_epub