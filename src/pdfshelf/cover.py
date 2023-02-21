import asyncio
import requests
import traceback
import time
import logging
import pdf2image
import ebooklib
from ebooklib import epub
from pathlib import Path
from typing import Callable
from .exceptions import FormatNotSupportedError
from .config import COVER_FOLDER
from .domain import Book

CoverExtractFunc = Callable[..., Path]
LOGGER = logging.getLogger(__name__)


class FileCoverExtractor:
    # TODO: Logging
    # TODO: Exception handling
    def __init__(self, cover_folder: Path | None = None):
        if cover_folder is None:
            self.cover_folder = COVER_FOLDER
        else:
            self.cover_folder = cover_folder

    def get_format_parser(self, fileformat: str) -> CoverExtractFunc:
        if fileformat == ".epub":
            return self._epub_extractor
        elif fileformat == ".pdf":
            return self._pdf_extractor
        else:
            raise FormatNotSupportedError("Format not supported.")

    def _pdf_extractor(self, hash_id: str, file: Path) -> Path:
        cover_path = self.cover_folder / f"cover_{hash_id}.jpg"

        pages = pdf2image.convert_from_path(file, first_page=1, last_page=1)
        pages[0].save(cover_path, 'JPEG')
        return cover_path

    def _epub_extractor(self, hash_id: str, file: Path) -> Path:
        cover_path = self.cover_folder / f"cover_{hash_id}.jpg"

        book = epub.read_epub(file)
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_COVER:
                with open(cover_path, 'wb') as cover:
                    cover.write(item.get_content())
                break
        return cover_path


class OLCoverFetcher:
    def __init__(self, cover_folder: Path | None = None,
                 rate_limiting: int = 85, waiting_time: float = 300):
        if cover_folder is None:
            self.cover_folder = COVER_FOLDER
        else:
            self.cover_folder = cover_folder

        self.rate_limiting = rate_limiting
        self.waiting_time = waiting_time

    def fetch(self, books: list[Book]) -> list[Book]:
        book_chunk = []
        chunk_size = 0
        processed_books = []

        for book in books:
            book_chunk.append(book)

            if book.isbn13 is None:
                continue

            chunk_size += 1
            if chunk_size % self.rate_limiting == 0:
                processed_books = [*processed_books,
                                   *asyncio.run(self._async_fetch(book_chunk))]
                book_chunk = []
                chunk_size = 0
                LOGGER.warning("Too many requests."
                               f" Waiting {self.waiting_time} seconds...")
                time.sleep(self.waiting_time)

        if len(book_chunk) != 0:
            processed_books = [*processed_books,
                               *asyncio.run(self._async_fetch(book_chunk))]
        return processed_books

    async def _async_fetch(self, books: list[Book]):
        return await asyncio.gather(
            *[self._async_fetch_cover(book) for book in books]
        )

    async def _async_fetch_cover(self, book: Book) -> Book:
        return await asyncio.to_thread(self._fetch_cover, book)

    def _fetch_cover(self, book: Book) -> Book:
        if book.isbn13 is None:
            LOGGER.warning("[COVER-FAILED] NO ISBN for "
                           f"{book.get_short_filename()}")
            return book

        size = 'L'
        isbn = book.isbn13
        url = f"https://covers.openlibrary.org/b/isbn/{isbn}-{size}.jpg?default=false"

        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 200:
                cover_path = self.cover_folder / f"cover_{book.hash_id}.jpg"

                with open(cover_path, 'wb') as file:
                    file.write(r.content)

                LOGGER.info(f"[COVER] Found for {book.get_short_filename()}")
                LOGGER.info(f"        Saved as {cover_path.name}")
                book.cover_path = cover_path
            else:
                LOGGER.warning("[COVER-FAILED] NOT Found for "
                               f"{book.get_short_filename()}")
        except requests.exceptions.Timeout:
            LOGGER.error(
                "[COVER-FAILED] OpenLibrary.com didn't responde.\n"
                f"{traceback.format_exc()}"
            )
        return book


class BookCover:

    def __init__(self, fetcher: OLCoverFetcher) -> None:
        pass
