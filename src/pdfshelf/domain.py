import json
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
    folder_id: int = None
    active: bool = True

    def __post_init__(self):
        if isinstance(self.path, str):
            self.path = Path(self.path)

        if isinstance(self.added_date, str):
            self.added_date = datetime.fromisoformat(self.added_date)

        if isinstance(self.active, int):
            self.active = True if self.active == 1 else False
        
    def get_parsed_dict(self) -> dict[str, Any]:
        d = { **self.__dict__ }
        d["path"] = str(d["path"])
        d["added_date"] = str(d["added_date"])
        d["active"] = 1 if d["active"] else 0
        return d

@dataclass(kw_only=True)
class Book:
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
    publisher: str
    added_date: datetime = datetime.now()
    book_id: int = None
    active: bool = True
    confirmed: bool = False
    isbn13: str = None
    parsed_isbn: str = None
    hash_id: str = None

    def __post_init__(self):
        if isinstance(self.authors, str):
            self.authors = json.loads(self.authors)
        
        if isinstance(self.storage_path, str):
            self.storage_path = Path(self.storage_path)

        if isinstance(self.folder, dict):
            self.folder = Folder(**self.folder)
        
        if isinstance(self.tags, str):
            self.tags = json.loads(self.tags)

        if isinstance(self.added_date, str):
            self.added_date = datetime.fromisoformat(self.added_date)
        
        if isinstance(self.active, int):
            self.active = True if self.active == 1 else False
       
        if isinstance(self.confirmed, int):
            self.confirmed = True if self.confirmed == 1 else False
        
        if self.hash_id is None:
            self.hash_id = hashlib.md5(self.filename.encode()).hexdigest()

    def get_absolute_path(self) -> Path:
        return self.folder.path / self.storage_path

    def get_parsed_dict(self) -> tuple[dict[str, Any], dict[str, Any]]:
        d = { **self.__dict__ }
        d["authors"] = json.dumps(d["authors"])
        d["storage_path"] = str(d["storage_path"])
        d["tags"] = json.dumps(d["tags"])
        d["added_date"] = str(d["added_date"])
        d["active"] = 1 if d["active"] else 0
        d["confirmed"] = 1 if d["confirmed"] else 0
        folder = d.pop("folder")
        return d, folder.get_parsed_dict()