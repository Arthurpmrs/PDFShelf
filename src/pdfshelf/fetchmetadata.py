import os
import re
import logging
import isbnlib
from pathlib import Path
from PyPDF2 import PdfReader
from .domain import Book, Paper
from .config import config_folder, default_document_folder
from .exceptions import FormatNotSupportedError
from .utilities import validade_isbn10, validate_isbn13

class MetadataFetcher:

    def __init__(self):
        self.setup_logging()

    def setup_logging(self):
        self.logger = logging.getLogger(__name__)

        if self.logger.hasHandlers():
            self.logger.handlers = []
            
        f_handler = logging.FileHandler(config_folder / "pdfshelf.log")
        self.logger.setLevel(logging.DEBUG)

        f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        f_handler.setFormatter(f_format)
        self.logger.addHandler(f_handler)

    def fetch_metadata_from_file(self, path) -> Book:
        if path.suffix == ".pdf":
            metadata = self._get_pdf_metadata(path)
        elif path.suffix == ".epub":
            metadata = self._get_epub_metadata()
        else:
            self.logger.error(f"{path.name} has a not supported format.")
            raise FormatNotSupportedError("Only PDF and EPUB are supported.")

        folder = {
            "name": "Default",
            "path": default_document_folder
        }

        book = Book(
            title=metadata["Title"],
            authors=metadata["Authors"],
            year=int(metadata["Year"]),
            publisher=metadata["Publisher"],
            lang=metadata["Language"],
            isbn13=metadata.get("ISBN-13", None),
            isbn10=metadata.get("ISBN-10", None),
            folder=folder,
            size=os.path.getsize(path),
            filename=path.name,
            ext=path.suffix,
            storage_path=default_document_folder,
        )
        return book

    def _get_pdf_metadata(self, path: Path, pages_to_read: int = 10) -> dict:
        re_ISBN = re.compile(r'(978-?|979-?)?\d(-?\d){9}')
        isbn10 = ""
        isbn13 = ""
        reader = PdfReader(path)
        pages = reader.pages[0:pages_to_read]
        for i, page in enumerate(pages):
            text = page.extract_text()
            isbn_mos = re_ISBN.finditer(text)
            if isbn_mos:
                for mo in isbn_mos:
                    match_str = mo.group()
                    if len(match_str.replace("-", "")) == 10 and validade_isbn10(match_str.replace("-", "")):
                        if not isbn10:
                            isbn10 = match_str
                    if len(match_str.replace("-", "")) == 13 and validate_isbn13(match_str.replace("-", "")):
                        if not isbn13:
                            isbn13 = match_str
        
        if isbn13:
            self.logger.info(f"ISBN-13: {isbn13} found for {path.name}.")
            metadata = isbnlib.meta(isbn13.replace("-", ""))
            if metadata:
                self.logger.info(f"Metadata found for {path.name}.")
                return metadata
            else:
                self.logger.warning(f"Metadata could not be found with ISBN-13 for {path.name}. Trying ISBN-10...")
        else:
            self.logger.warning(f"ISBN-13 not found. Trying ISBN-10...")
        
        if isbn10:
            self.logger.info(f"ISBN-10: {isbn10} found for {path.name}.")
            metadata = isbnlib.meta(isbn10.replace("-", ""))
            if metadata:
                self.logger.info(f"Metadata found for {path.name}.")
                return metadata
        
        self.logger.error(f"Metadata not fount for {path.name}")