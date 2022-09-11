import os
from pathlib import Path
config_folder = Path(os.path.expanduser("~")) / ".config" / "pdfshelf"
config_folder.mkdir(exist_ok=True)