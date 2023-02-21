from pathlib import Path
from pdfshelf.cover import FileCoverExtractor
from pdfshelf.importer import book_from_file
from pdfshelf.config import COVER_FOLDER


class TestFileCoverExtractor:

    def test_extract_from_pdf(self, tmp_path):
        filename = "Amol M. Jagtap, Ajit S. Mali - Data Structures using C_ A Practical Approach for Beginners-Chapman and Hall_CRC (2021).pdf"
        path = Path("/home/arthurpmrs/books") / filename

        book = book_from_file(path)

        fake_cover_folder = tmp_path / "cover"
        fake_cover_folder.mkdir()

        cover_extractor = FileCoverExtractor(fake_cover_folder)
        extract_func = cover_extractor.get_format_parser(book.ext)

        cover_path = extract_func(book.hash_id, book.get_full_path())
        expected_cover_path = COVER_FOLDER / f"cover_{book.hash_id}.jpg"
        assert expected_cover_path.exists() == True
