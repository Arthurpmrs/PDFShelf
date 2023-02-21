import logging
import pdf2image
import ebooklib
from ebooklib import epub
from pathlib import Path
from typing import Callable
from .exceptions import FormatNotSupportedError
from .config import COVER_FOLDER


CoverExtractFunc = Callable[..., Path]
LOGGER = logging.getLogger(__name__)


class FileCoverExtractor:

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

    def __init__(self) -> None:
        pass


class BookCover:

    def __init__(self, fetcher: OLCoverFetcher) -> None:
        pass
