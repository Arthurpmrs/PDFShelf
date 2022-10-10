import hashlib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Any
@dataclass
class Folder:
    name:str
    path: Path
    added_date: datetime = datetime.now()
    active: bool = True

    def __post_init__(self):
        if isinstance(self.path, str):
            self.path = Path(self.path)

        if isinstance(self.added_date, str):
            self.added_date = datetime.fromisoformat(self.added_date)
        
    def get_parsed_dict(self) -> dict[str, Any]:
        d = { **self.__dict__ }
        d["path"] = str(d["path"])
        d["added_date"] = str(d["added_date"])
        d["active"] = 1 if d["active"] else 0
        return d

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
    tags: list[str]
    added_date: datetime = datetime.now()
    hash_id: str = ""
    active: bool = True
    confirmed: bool = False

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

    def get_parsed_dict(self) -> tuple[dict[str, Any], dict[str, Any]]:
        d = { **self.__dict__ }
        d["authors"] = str(d["authors"])
        d["storage_path"] = str(d["storage_path"])
        d["tags"] = str(d["tags"])
        d["added_date"] = str(d["added_date"])
        d["active"] = 1 if d["active"] else 0
        d["confirmed"] = 1 if d["confirmed"] else 0
        folder = d.pop("folder")
        return d, folder.get_parsed_dict()

@dataclass
class Book(Document):
    publisher: str
    isbn10: str = None
    isbn13: str = None
    parsed_isbn: str = None


@dataclass
class Paper(Document):
    journal:str
    doi: str
    pages:tuple[int,int] = None
    volume:int = None
    issn: str = None
    edition: int = None
