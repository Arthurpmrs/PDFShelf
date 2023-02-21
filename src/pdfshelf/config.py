import os
import configparser
from pathlib import Path

user_folder = Path(os.path.expanduser("~"))
config_folder = user_folder / ".config" / "pdfshelf"
config_folder.mkdir(exist_ok=True)


def create_base_config_file() -> None:
    config_file_path = config_folder / "config.ini"
    if config_file_path.exists():
        return

    default_document_folder = user_folder / "Documents" / "PDFShelf"
    conf = configparser.ConfigParser()
    conf["DEFAULT"] = {
        "default_document_folder": str(default_document_folder),
        "cover_folder": str(default_document_folder / "cover")
    }

    with open(config_file_path, 'w') as configfile:
        conf.write(configfile)


create_base_config_file()
config = configparser.ConfigParser()
config.sections()
config.read(config_folder / "config.ini")

default_document_folder = Path(config["DEFAULT"]["default_document_folder"])
default_document_folder.mkdir(exist_ok=True)
COVER_FOLDER = Path(config["DEFAULT"]["cover_folder"])
COVER_FOLDER.mkdir(exist_ok=True)
