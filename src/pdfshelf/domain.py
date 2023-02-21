import json
import hashlib
from typing import Any
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass


@dataclass(kw_only=True)
class Folder:
    folder_id: int | None = None
    name: str
    path: Path
    added_date: datetime = datetime.now()
    active: bool = True

    @classmethod
    def from_raw_data(cls, data: dict[str, Any]):
        if isinstance(data.get("path"), str):
            data["path"] = Path(data["path"])

        if isinstance(data.get("added_date"), str):
            data["added_date"] = datetime.fromisoformat(data["added_date"])

        if isinstance(data.get("active"), int):
            data["active"] = True if data["active"] == 1 else False

        return cls(**data)

    def get_parsed_dict(self) -> dict[str, Any]:
        d = {**self.__dict__}
        d["path"] = str(d["path"])
        d["active"] = 1 if d["active"] else 0
        return d


@ dataclass(kw_only=True)
class Book:
    book_id: int | None = None
    hash_id: str | None = None
    title: str | None
    authors: list[str]
    year: int | None
    lang: str | None
    publisher: str | None
    isbn13: str | None
    parsed_isbn: str | None
    folder: Folder
    filename: str
    ext: str
    storage_path: Path
    size: float
    tags: list[str]
    added_date: datetime = datetime.now()
    cover_path: Path | None
    active: bool = True
    confirmed: bool = False

    def __post_init__(self):
        if self.hash_id is None:
            self.hash_id = hashlib.md5(self.filename.encode()).hexdigest()

    @classmethod
    def from_raw_data(cls, data: dict[str, Any]):
        if isinstance(data.get("authors"), str):
            data["authors"] = json.loads(data["authors"])

        if isinstance(data.get("storage_path"), str):
            data["storage_path"] = Path(data["storage_path"])

        if isinstance(data.get("cover_path"), str):
            data["cover_path"] = Path(data["cover_path"])

        if isinstance(data.get("tags"), str):
            data["tags"] = json.loads(data["tags"])

        if isinstance(data.get("added_date"), str):
            data["added_date"] = datetime.fromisoformat(data["added_date"])

        if isinstance(data.get("active"), int):
            data["active"] = True if data["active"] == 1 else False

        if isinstance(data.get("confirmed"), int):
            data["confirmed"] = True if data["confirmed"] == 1 else False

        if isinstance(data.get("folder"), dict):
            data["folder"] = Folder.from_raw_data(data["folder"])

        return cls(**data)

    def get_parsed_dict(self) -> tuple[dict[str, Any], dict[str, Any]]:
        d = {**self.__dict__}
        d["authors"] = json.dumps(d["authors"])
        d["storage_path"] = str(d["storage_path"])
        if (d["cover_path"]) is not None:
            d["cover_path"] = str(d["cover_path"])
        d["tags"] = json.dumps(d["tags"])
        d["active"] = 1 if d["active"] else 0
        d["confirmed"] = 1 if d["confirmed"] else 0
        folder = d.pop("folder")
        d["folder_id"] = folder.folder_id
        return d, folder.get_parsed_dict()

    def get_short_filename(self, size: int = 40) -> str:
        if len(self.filename) > size:
            return f"{self.filename[:size - 3]}..."
        else:
            return self.filename
