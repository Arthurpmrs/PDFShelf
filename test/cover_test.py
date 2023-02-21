from pathlib import Path
import pytest
from pdfshelf.cover import FileCoverExtractor
from pdfshelf.importer import book_from_file
from pdfshelf.config import COVER_FOLDER


class TestFileCoverExtractor:

    def test_extract_pdf_file(self, tmp_path):
        filename = "Robert Sedgewick, Kevin Wayne - Algorithms-Addison-Wesley Professional (2011).pdf"
        filename = "Amol M. Jagtap, Ajit S. Mali - Data Structures using C_ A Practical Approach for Beginners-Chapman and Hall_CRC (2021).pdf"
        path = Path("/home/arthurpmrs/books") / filename

        book = book_from_file(path)
        book.folder.path = Path("/home/arthurpmrs/books")
        fake_cover_folder = tmp_path / "cover"
        fake_cover_folder.mkdir()
        extract_func = (
            FileCoverExtractor(fake_cover_folder)
            .get_format_parser(book.ext)
        )
        cover_path = extract_func(book.hash_id, book.get_full_path())
        expected_cover_path = COVER_FOLDER / f"cover_{book.hash_id}.jpg"
        assert expected_cover_path.exists() == True
