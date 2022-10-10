import os
from pathlib import Path
user_folder = Path(os.path.expanduser("~"))
config_folder = user_folder / ".config" / "pdfshelf"
config_folder.mkdir(exist_ok=True)
# Create a config file with config parser to make possible to alter this values. For now:
default_document_folder = user_folder / "Documents" / "PDFShelf"
default_document_folder.mkdir(exist_ok=True)