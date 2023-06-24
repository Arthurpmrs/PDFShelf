import os
import re
import logging
import isbnlib
import ebooklib
import traceback
from typing import Callable
from isbnlib import ISBNLibException
from ebooklib import epub
from ebooklib.epub import EpubException
from pathlib import Path
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from .domain import Book, Folder
from .exceptions import FormatNotSupportedError
from .utilities import validade_isbn10, validate_isbn13

ParserFunc = Callable[..., tuple[str, str]]

FORMATS = [".pdf", ".epub"]


def book_from_file(file: Path) -> Book:
    """
    High-Level function to get Book objects with metadata from 
    a local PDF or EPUB file.

    input:
        file: Path

    return:
        Book
    """
    parser = ISBNParser(pages_to_read=10)
    fetcher = MetadataFetcher()
    importer = BookImporter(fetcher, parser)
    return importer.import_from_file(file)


def books_from_folder(folder: Folder) -> list[Book]:
    """
    High-Level function to get a list of Book objects with metadata from 
    a local folder.

    input:
        folder: Folder

    return:
        list[Book]
    """

    parser = ISBNParser(pages_to_read=10)
    fetcher = MetadataFetcher()
    importer = BookImporter(fetcher, parser)
    return importer.import_from_folder(folder)


class ISBNParser:
    RE_ISBN = re.compile(r'(978-?|979-?)?\d(-?[\dxX]){9}')

    def __init__(self, pages_to_read: int = 10) -> None:
        self.logger = logging.getLogger(__name__)
        self.pages_to_read = pages_to_read

    def get_format_parser(self, fileformat: str) -> ParserFunc:
        if fileformat == ".epub":
            return self._epub_parser
        elif fileformat == ".pdf":
            return self._pdf_parser
        else:
            raise FormatNotSupportedError("Format not supported.")

    def _epub_parser(self, filepath: Path) -> tuple[str, str]:
        isbn10 = ""
        isbn13 = ""
        try:
            book = epub.read_epub(filepath)
        except EpubException:
            self.logger.error(
                "EPUB file is probably corrupted!\n"
                f"{traceback.format_exc()}"
            )
            return "", ""

        # Get ISBN from metadata.
        identifier = book.get_metadata("DC", "identifier")[0][0]
        filtered_identifier = "".join(filter(str.isdigit, identifier))
        if len(filtered_identifier) == 10 and validade_isbn10(filtered_identifier):
            isbn10 = filtered_identifier
        if len(filtered_identifier) == 13 and validate_isbn13(filtered_identifier):
            isbn13 = filtered_identifier

        # Get ISBN with REGEX if needed.
        if isbn10 == "" and isbn13 == "":
            docs = book.get_items_of_type(ebooklib.ITEM_DOCUMENT)
            html_pile = ""
            for i, html in enumerate(docs):
                if i > self.pages_to_read:
                    break
                html_pile += str(html.get_body_content())

            isbn_mos = self.RE_ISBN.finditer(html_pile)

            for mo in isbn_mos:
                match_str = mo.group()
                if len(match_str.replace("-", "")) == 10 and validade_isbn10(match_str.replace("-", "")):
                    if not isbn10:
                        isbn10 = match_str
                if len(match_str.replace("-", "")) == 13 and validate_isbn13(match_str.replace("-", "")):
                    if not isbn13:
                        isbn13 = match_str

        return isbn10, isbn13

    def _pdf_parser(self, filepath: Path) -> tuple[str, str]:
        isbn10 = ""
        isbn13 = ""

        try:
            reader = PdfReader(filepath)
        except PdfReadError:
            self.logger.error(
                "PDF file is probably corrupted!"
                f"\n{traceback.format_exc()}"
            )
            return "", ""

        pages = reader.pages[0:self.pages_to_read]
        for i, page in enumerate(pages):
            text = page.extract_text()
            isbn_mos = self.RE_ISBN.finditer(text)
            if isbn_mos:
                for mo in isbn_mos:
                    match_str = mo.group()
                    if len(match_str.replace("-", "")) == 10 and validade_isbn10(match_str.replace("-", "")):
                        if not isbn10:
                            isbn10 = match_str
                    if len(match_str.replace("-", "")) == 13 and validate_isbn13(match_str.replace("-", "")):
                        if not isbn13:
                            isbn13 = match_str

        return isbn10, isbn13


class MetadataFetcher:

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def from_isbn(self, isbn10: str, isbn13: str) -> tuple[dict, bool]:
        if isbn13:
            self.logger.info(f"ISBN-13: {isbn13} found.")
            try:
                metadata = isbnlib.meta(isbn13.replace("-", ""))
            except ISBNLibException:
                self.logger.error(
                    "ISBNLib metadata fetching failed!\n"
                    f"{traceback.format_exc()}"
                )
                return {}, False

            if metadata:
                self.logger.info(f"Metadata found with ISBN-13!")
                metadata = {
                    **metadata,
                    "parsed_isbn": isbn13
                }
                return metadata, True
            else:
                self.logger.info(
                    "Metadata could not be found with ISBN-13. "
                    "Trying ISBN-10..."
                )
        else:
            self.logger.info(f"ISBN-13 not found. Trying ISBN-10...")

        if isbn10:
            self.logger.info(f"ISBN-10: {isbn10} found.")
            try:
                metadata = isbnlib.meta(isbn10.replace("-", ""))
            except ISBNLibException:
                self.logger.error(
                    "ISBNLib metadata fetching failed!\n"
                    f"{traceback.format_exc()}"
                )
                return {}, False

            if metadata:
                self.logger.info(f"Metadata found with ISBN-10!")
                metadata = {
                    **metadata,
                    "parsed_isbn": isbn10
                }
                return metadata, True
            else:
                self.logger.warning(
                    "Metadata could not be found. "
                    "Manual Metadata is required."
                )
                return {}, False
        else:
            self.logger.warning(
                "ISBN-10 not found as well. "
                "Manual Metadata is required."
            )
            return {}, False


class BookImporter:
    def __init__(self, fetcher: MetadataFetcher, parser: ISBNParser) -> None:
        self.logger = logging.getLogger(__name__)
        self.fetcher = fetcher
        self.parser = parser

    def import_from_file(self, file: Path, folder: Folder | None = None) -> Book:
        """"""
        if not file.is_file():
            self.logger.error(f"File: {file} does not exists.")
            raise FileNotFoundError("Provided file does not exists.")

        parse_function = self.parser.get_format_parser(file.suffix)
        isbn10, isbn13 = parse_function(file)

        metadata, success = self.fetcher.from_isbn(isbn10, isbn13)

        if folder is None:
            folder = Folder.from_raw_data({
                "name": file.parent.name,
                "path": file.parent
            })

        year = metadata.get("Year", "0")
        book = Book.from_raw_data({
            "title": metadata.get("Title"),
            "authors": metadata.get("Authors", []),
            "year": None if year == "0" else int(year),
            "lang": metadata.get("Language"),
            "publisher": metadata.get("Publisher"),
            "isbn13": metadata.get("ISBN-13"),
            "parsed_isbn": metadata.get("parsed_isbn"),
            "folder": folder,
            "filename": file.name,
            "ext": file.suffix,
            "storage_path": file.relative_to(folder.path),
            "size": os.path.getsize(file),
            "tags": [],
            "cover_path": None
        })
        return book

    def import_from_folder(self, folder: Folder) -> list[Book]:
        """"""
        if not folder.path.is_dir():
            self.logger.error(f"Folder: {folder.path} does not exists.")
            raise FileNotFoundError("This directory does not exist.")

        books = []
        for filepath in folder.path.rglob("*"):
            if filepath.suffix in FORMATS:
                book_data = self.import_from_file(filepath, folder)
                books.append(book_data)
        return books
