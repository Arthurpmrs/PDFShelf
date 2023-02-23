from datetime import datetime
from typing import Any
from pdfshelf.domain import Book, Folder


def validade_isbn10(isbn: str) -> bool:
    """Checks if a number sequence is a valid ISBN-10. Ref: https://en.wikipedia.org/wiki/ISBN"""
    s = 0
    for i, char in enumerate(isbn):
        if char.lower() == "x":
            s += (10 - i) * 10
        else:
            s += (10 - i) * int(char)

    if s % 11 == 0:
        is_valid = True
    else:
        is_valid = False

    return is_valid


def validate_isbn13(isbn: str) -> bool:
    """Checks if a number sequence is a valid ISBN-13. Ref: https://en.wikipedia.org/wiki/ISBN"""
    s = 0
    for i, char in enumerate(isbn):
        if i % 2 == 0:
            s += 1 * int(char)
        else:
            s += 3 * int(char)

    if s % 10 == 0:
        is_valid = True
    else:
        is_valid = False

    return is_valid


class _Auto:
    """
    Sentinel value indicating an automatic default will be used.
    Ref: https://lukeplant.me.uk/blog/posts/test-factory-functions-in-django/
    """

    def __bool__(self):
        return False


Auto: Any = _Auto()


def folder_factory(
    *, name: str = "folder-000", path: str = "/home/username/Documents/Books",
    added_date: datetime = Auto, folder_id: int = Auto, active: int = True
) -> Folder:
    folder = Folder.from_raw_data({
        "name": name,
        "path": path,
        "added_date": datetime.now() if added_date is Auto else added_date,
        "folder_id": None if folder_id is Auto else folder_id,
        "active": active
    })
    return folder


def book_factory(
    *, title: str = "TheBookTM", authors: list[str] = Auto, year: int = 2021,
    publisher: str = "ThePublisherTM", lang: str = "en",
    isbn13: str = "9781593275990", parsed_isbn: str = "9781593275990",
    folder: Folder = Auto, size: float = 12001.1, tags: list[str] = Auto,
    filename: str = "the_book_tm.pdf", ext: str = ".pdf",
    storage_path: str = "genericbooks/the_book_tm.pdf",
    cover_path: str = "/home/arthurpmrs/pdfshelf/covers/cover_1.jpg",
    active: bool = True, confirmed: bool = False, hash_id: str = Auto,
    book_id: int = Auto
) -> Book:

    if authors is Auto:
        authors = ["Plato", "Socrates"]
    if folder is Auto:
        folder = folder_factory()
    if tags is Auto:
        tags = ["Philosofy", "Mystic"]

    book = Book.from_raw_data({
        "title": title,
        "authors": authors,
        "year": year,
        "lang": lang,
        "publisher": publisher,
        "isbn13": isbn13,
        "parsed_isbn": parsed_isbn,
        "folder": folder,
        "filename": filename,
        "ext": ext,
        "storage_path": storage_path,
        "size": size,
        "tags": tags,
        "cover_path": cover_path,
        "book_id": None if book_id is Auto else book_id,
        "hash_id": None if hash_id is Auto else hash_id,
    })
    return book
