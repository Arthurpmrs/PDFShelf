import hashlib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

@dataclass
class Folder:
    name:str
    path: Path
    active: bool = True

    def __post_init__(self):
        if isinstance(self.path, str):
            self.path = Path(self.path)

@dataclass(kw_only=True)
class Document:
    title: str
    authors: list[str]
    year: int
    lang: str
    filename:str
    ext:str
    storage_path: Path
    folder: Folder
    size: float
    added_date: datetime = datetime.now()
    hash_id: str = ""
    active: bool = True

    def __post_init__(self):
        if isinstance(self.storage_path, str):
            self.storage_path = Path(self.storage_path)

        if isinstance(self.added_date, str):
            self.added_date = datetime.fromisoformat(self.added_date)

        if isinstance(self.folder, dict):
            self.folder = Folder(**self.folder)

        if self.hash_id == "":
            self.hash_id = hashlib.md5(self.filename.encode()).hexdigest()

    def get_absolute_path(self) -> Path:
        return self.folder.path / self.storage_path


@dataclass
class Book(Document):
    publisher: str
    isbn10: str = None
    isbn13: str = None


@dataclass
class Paper(Document):
    journal:str
    doi: str
    pages:tuple[int,int] = None
    volume:int = None
    issn: str = None
    edition: int = None


if __name__ == "__main__":
    folder = {
        "name": "foldinha",
        "path": "/home/Documents/Library/Livros"
    }

    book = Book(
        title="Modeling and simulation in Python",
        authors=["Jason M. Kinser"],
        year=2022,
        lang="en",
        filename="Jason M. Kinser - Modeling and Simulation in Python-Chapman & Hall (2022).pdf",
        ext="pdf",
        storage_path="teste/Jason M. Kinser - Modeling and Simulation in Python-Chapman & Hall (2022).pdf",
        folder=folder,
        size=100000,
        publisher="CRC Press",
        isbn13="978-1-032-11648-8"
    )


    print(book)
    print(book.folder)