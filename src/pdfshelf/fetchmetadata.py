import os
import re
import logging
import isbnlib
import ebooklib
import traceback
from isbnlib import ISBNLibException
from ebooklib import epub
from ebooklib.epub import EpubException
from pathlib import Path
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
from .domain import Book
from .config import config_folder, default_document_folder
from .exceptions import FormatNotSupportedError
from .utilities import validade_isbn10, validate_isbn13

class MetadataFetcher:
    FORMATS = [".pdf", ".epub"]
    RE_ISBN = re.compile(r'(978-?|979-?)?\d(-?[\dxX]){9}')

    def __init__(self, pages_to_read: int = 10):
        self.logger = logging.getLogger(__name__)
        self.pages_to_read = pages_to_read

    def get_books_from_folder(self, folderpath: Path) -> tuple[list[tuple[Book, bool]], int]:
        if not folderpath.is_dir():
            self.logger.error(f"Folder: {folderpath} does not exists.")
            raise FileNotFoundError("This directory does not exist.")
        
        books = []
        success_count = 0
        folder = {"name": folderpath.name, "path": folderpath}
        for filepath in folderpath.rglob("*"):
            if filepath.suffix in MetadataFetcher.FORMATS:
                book_data = self.get_book_from_file(filepath, folder)
                books.append(book_data)
                success_count += 1 if book_data[1] else 0
        return books, success_count

    def get_book_from_file(self, path: Path, folder: dict = None) -> tuple[Book, bool]:
        if not path.is_file():
            self.logger.error(f"File: {path} does not exists.")
            raise FileNotFoundError("This file does not exists.")

        metadata, success = self._fetch_metadata(path)

        if folder:
            storage_path = path.relative_to(folder["path"])
        else:
            storage_path = path.name
            folder = {
                "name": "Default",
                "path": default_document_folder
            }
        
        year = metadata.get("Year", "0")
        book = Book(
            title=metadata.get("Title", None),
            authors=metadata.get("Authors", []),
            year=None if year == "0" else int(year),
            publisher=metadata.get("Publisher", None),
            lang=metadata.get("Language", None),
            isbn13=metadata.get("ISBN-13", None),
            parsed_isbn=metadata.get("parsed_isbn", None),
            folder=folder,
            size=os.path.getsize(path),
            tags=[],
            filename=path.name,
            ext=path.suffix,
            storage_path=storage_path,
        )
        return book, success

    def _fetch_metadata(self, path: Path) -> tuple[dict, bool]:
        if path.suffix == ".pdf":
            isbn10, isbn13 = self._get_isbn_from_pdf(path)
        elif path.suffix == ".epub":
            isbn10, isbn13 = self._get_isbn_from_epub(path)
        else:
            self.logger.error(f"{path.name} has a not supported format.")
            raise FormatNotSupportedError("Only PDFs and EPUBs are supported.")

        self.logger.info(f"Fetching data for {path.name}")
        if isbn13:
            self.logger.info(f"ISBN-13: {isbn13} found.")

            try:
                metadata = isbnlib.meta(isbn13.replace("-", ""))
            except ISBNLibException:
                self.logger.error(f"ISBNLib metadata fetching failed!\n{traceback.format_exc()}")
                return {}, False
            
            if metadata:
                self.logger.info(f"Metadata found with ISBN-13!")
                metadata.update({"parsed_isbn": isbn13})
                return metadata, True
            else:
                self.logger.info(f"Metadata could not be found with ISBN-13. Trying ISBN-10...")
        else:
            self.logger.info(f"ISBN-13 not found. Trying ISBN-10...")
        
        if isbn10:
            self.logger.info(f"ISBN-10: {isbn10} found.")
            try:
                metadata = isbnlib.meta(isbn10.replace("-", ""))
            except ISBNLibException:
                self.logger.error(f"ISBNLib metadata fetching failed!\n{traceback.format_exc()}")
                return {}, False

            if metadata:
                self.logger.info(f"Metadata found with ISBN-10!")
                metadata.update({"parsed_isbn": isbn10})
                return metadata, True
            else:
                self.logger.warning(f"Metadata could not be found. Manual Metadata is required.")
                return {}, False
        else:
            self.logger.warning(f"ISBN-10 not found as well. Manual Metadata is required.")
            return {}, False

    def _get_isbn_from_pdf(self, path:Path) -> tuple[str, str]:
        isbn10 = ""
        isbn13 = ""
        
        try:
            reader = PdfReader(path)
        except PdfReadError:
            self.logger.error(f"PDF file is probably corrupted!\n{traceback.format_exc()}")
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
    
    def _get_isbn_from_epub(self, path:Path) -> tuple[str, str]:
        isbn10 = ""
        isbn13 = ""
        try:
            book = epub.read_epub(path)
        except EpubException:
            self.logger.error(f"EPUB file is probably corrupted!\n{traceback.format_exc()}")
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