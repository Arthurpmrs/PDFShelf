import os
import pytest
from typing import Any
from pathlib import Path
from isbnlib import ISBNLibException
from pdfshelf.domain import Book, Folder
from pdfshelf.importer import BookImporter, MetadataFetcher, ISBNParser
from pdfshelf.exceptions import FormatNotSupportedError


class MockMetadataFetcher(MetadataFetcher):
    def __init__(self, mock_data: Any = None):
        self.mock_data = mock_data

    def from_isbn(self, isbn10: str, isbn13: str) -> tuple[dict, bool]:
        if isbn13:
            parsed_isbn = isbn13
        elif isbn10:
            parsed_isbn = isbn10
        else:
            parsed_isbn = None

        if self.mock_data is None:
            return {}, False
        else:
            result = {
                "Title": "Mocking a PDF",
                "Authors": ["Mockerson Mock", "Mockiney Mockares"],
                "Year": 2012,
                "Publisher": "John Mock and Sons",
                "Language": "en",
                "ISBN-13": "9780999773017",
                "parsed_isbn": parsed_isbn
            }
            result.update(self.mock_data)
            return result, True


class MockISBNParser(ISBNParser):
    def __init__(self, isbn10: str, isbn13: str):
        self.isbn10 = isbn10
        self.isbn13 = isbn13

    def _epub_parser(self, filepath: Path) -> tuple[str, str]:
        return self.isbn10, self.isbn13

    def _pdf_parser(self, filepath: Path) -> tuple[str, str]:
        return self.isbn10, self.isbn13


@pytest.fixture
def rootdir():
    return os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def importer():
    fetcher = MockMetadataFetcher({})
    parser = MockISBNParser("", "")
    return BookImporter(fetcher, parser)


class TestBookImporter:

    def test_get_books_from_missing_folder(self, importer, tmp_path) -> None:
        not_created_dir = tmp_path / "folder1"

        with pytest.raises(FileNotFoundError):
            importer.import_from_folder(not_created_dir)

    def test_get_books_from_empty_folder(self, importer, tmp_path) -> None:
        tmp_dir = tmp_path / "folder"
        tmp_dir.mkdir()
        books = importer.import_from_folder(tmp_dir)
        assert len(books) == 0

    def test_get_book_from_missing_files(self, importer, tmp_path) -> None:
        non_existing_pdf = tmp_path / "folder" / "file.pdf"
        non_existing_epub = tmp_path / "folder" / "file.epub"

        with pytest.raises(FileNotFoundError):
            importer.import_from_file(non_existing_pdf)

        with pytest.raises(FileNotFoundError):
            importer.import_from_file(non_existing_epub)

    def test_failed_fetching_metadata(self, rootdir, mocker) -> None:
        files = [
            os.path.join(rootdir,
                         'test_data/how_to_code_in_python_isbn13.pdf'),
            os.path.join(rootdir, 'test_data/craft-isbn-13.epub'),
            os.path.join(rootdir, 'test_data/php5_isbn10.pdf'),
            os.path.join(rootdir, 'test_data/git-magic-isbn-10.epub')
        ]

        fetcher = MockMetadataFetcher(None)
        parser = MockISBNParser("", "")
        importer = BookImporter(fetcher, parser)
        for file in files:
            book = importer.import_from_file(Path(file))
            assert book.title is None
            assert book.isbn13 is None
            assert book.year is None

    def test_get_book_invalid_file_format(self, tmp_path) -> None:
        tmp_folder = tmp_path / "test_folder"
        tmp_folder.mkdir()

        tmp_file = tmp_folder / "file.txt"
        tmp_file.write_text("hello_world")

        fetcher = MockMetadataFetcher({})
        parser = ISBNParser()
        importer = BookImporter(fetcher, parser)

        with pytest.raises(FormatNotSupportedError):
            importer.import_from_file(Path(tmp_file))


class TestPDFISBNParser:
    def test_get_book_from_file_pdf_isbn13(self, rootdir) -> None:
        test_file = os.path.join(rootdir,
                                 'test_data/how_to_code_in_python_isbn13.pdf')
        expected_isbn = "978-0-9997730-1-7"

        fetcher = MockMetadataFetcher({})
        parser = ISBNParser()
        importer = BookImporter(fetcher, parser)
        book = importer.import_from_file(Path(test_file))

        assert book.ext == ".pdf"
        assert book.filename == "how_to_code_in_python_isbn13.pdf"
        assert book.parsed_isbn == expected_isbn
        assert book.storage_path == Path("how_to_code_in_python_isbn13.pdf")

    def test_get_book_from_file_pdf_isbn10(self, rootdir, mocker) -> None:
        test_file = os.path.join(rootdir, 'test_data/php5_isbn10.pdf')
        expected_isbn = "0-131-47149-X"

        fetcher = MockMetadataFetcher({})
        parser = ISBNParser()
        importer = BookImporter(fetcher, parser)
        book = importer.import_from_file(Path(test_file))

        assert book.ext == ".pdf"
        assert book.filename == "php5_isbn10.pdf"
        assert book.parsed_isbn == expected_isbn
        assert book.storage_path == Path("php5_isbn10.pdf")

    def test_get_book_from_file_pdf_no_valid_isbn(self, rootdir) -> None:
        test_file = os.path.join(rootdir,
                                 'test_data/think_python_2_no_isbn.pdf')
        expected_isbn = None

        fetcher = MockMetadataFetcher()
        parser = ISBNParser()
        importer = BookImporter(fetcher, parser)
        book = importer.import_from_file(Path(test_file))

        assert book.ext == ".pdf"
        assert book.filename == "think_python_2_no_isbn.pdf"
        assert book.parsed_isbn == expected_isbn
        assert book.storage_path == Path("think_python_2_no_isbn.pdf")

    def test_get_book_from_file_corrupted_pdf(self, rootdir) -> None:
        test_file = os.path.join(rootdir, 'test_data/corrupted.pdf')
        expected_isbn = None

        fetcher = MockMetadataFetcher()
        parser = ISBNParser()
        importer = BookImporter(fetcher, parser)
        book = importer.import_from_file(Path(test_file))

        assert book.ext == ".pdf"
        assert book.parsed_isbn == expected_isbn


class TestEPUBISBNParser:
    def test_get_book_from_file_epub_isbn13(self, rootdir) -> None:
        test_file = os.path.join(rootdir, 'test_data/craft-isbn-13.epub')
        expected_isbn = "978-1-4116-8297-9"

        fetcher = MockMetadataFetcher({})
        parser = ISBNParser()
        importer = BookImporter(fetcher, parser)
        book = importer.import_from_file(Path(test_file))

        assert book.ext == ".epub"
        assert book.filename == "craft-isbn-13.epub"
        assert book.parsed_isbn == expected_isbn
        assert book.storage_path == Path("craft-isbn-13.epub")

    def test_get_book_from_file_epub_isbn10(self, rootdir) -> None:
        test_file = os.path.join(rootdir, 'test_data/git-magic-isbn-10.epub')
        expected_isbn = "1451523343"

        fetcher = MockMetadataFetcher({})
        parser = ISBNParser()
        importer = BookImporter(fetcher, parser)
        book = importer.import_from_file(Path(test_file))

        assert book.ext == ".epub"
        assert book.filename == "git-magic-isbn-10.epub"
        assert book.parsed_isbn == expected_isbn
        assert book.storage_path == Path("git-magic-isbn-10.epub")

    def test_get_book_from_file_epub_no_valid_isbn(self, rootdir) -> None:
        test_file = os.path.join(rootdir,
                                 'test_data/beginners-in-open-source-no-isbn.epub')
        expected_isbn = None

        fetcher = MockMetadataFetcher()
        parser = ISBNParser()
        importer = BookImporter(fetcher, parser)
        book = importer.import_from_file(Path(test_file))

        assert book.ext == ".epub"
        assert book.filename == "beginners-in-open-source-no-isbn.epub"
        assert book.parsed_isbn == expected_isbn
        assert book.storage_path == Path(
            "beginners-in-open-source-no-isbn.epub"
        )

    def test_get_book_from_file_corrupted_epub(self, rootdir) -> None:
        test_file = os.path.join(rootdir, 'test_data/corrupted.epub')

        expected_isbn = None

        fetcher = MockMetadataFetcher()
        parser = ISBNParser()
        importer = BookImporter(fetcher, parser)
        book = importer.import_from_file(Path(test_file))

        print(book)
        assert book.ext == ".epub"
        assert book.parsed_isbn == expected_isbn

    def test_get_book_from_file_api_failed(self, rootdir, mocker) -> None:
        test_file = os.path.join(
            rootdir, 'test_data/how_to_code_in_python_isbn13.pdf')

        mocker.patch(
            "pdfshelf.importer.isbnlib.meta",
            side_effect=ISBNLibException("ISBN API Failed!")
        )

        fetcher = MetadataFetcher()
        parser = ISBNParser()
        importer = BookImporter(fetcher, parser)
        book = importer.import_from_file(Path(test_file))

        assert book.title == None
        assert book.year == None
        assert book.isbn13 == None
        assert book.parsed_isbn == None
