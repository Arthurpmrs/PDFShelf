import logging
import time
from pathlib import Path
from dataclasses import dataclass
from src.pdfshelf.domain import Folder
from src.pdfshelf.importer import books_from_folder
from src.pdfshelf.config import config_folder
from src.pdfshelf.database import DatabaseConnector, BookDBHandler, FolderDBHandler
from src.pdfshelf.importer import books_from_folder
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse


@dataclass
class FolderRequestBody:
    name: str
    path: str


app = FastAPI()
logger = logging.getLogger(__name__)


templates = Jinja2Templates(directory="src/templates")
app.mount("/static", StaticFiles(directory="src/static"), name="static")
app.mount("/node_modules",
          StaticFiles(directory="node_modules"), name="node_modules")


@app.get("/home", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/folders", response_class=HTMLResponse)
def folders(request: Request):
    with DatabaseConnector() as con:
        folder_handler = FolderDBHandler(con)
        folders = folder_handler.load_folders()

    return templates.TemplateResponse("folders.html",
                                      {"request": request, "folders": folders})


@app.post("/folders/add")
def add_folder(folderRB: FolderRequestBody):
    if folderRB.path == "":
        logger.warning("No path provided.")
        return {"success": False, "message": "No path provided."}

    folder_path = Path(folderRB.path)
    if folder_path.exists() == False:
        logger.warning("Folder does not exist.")
        return {"success": False, "message": "Folder does not exist."}

    folder_name = folderRB.name
    if folderRB.name == "":
        folder_name = folder_path.name

    folder = Folder.from_raw_data({
        "path": folder_path,
        "name": folder_name,
        "active": 1
    })

    with DatabaseConnector() as con:
        # Insert the folder
        folder_handler = FolderDBHandler(con)
        if folder_handler.is_path_duplicate(folder):
            logger.warning("Folder already exists in db.")
            return {"success": False, "message": "Folder already exists in db."}

        if folder_handler.is_name_duplicate(folder):
            folder.name = f"{round(time.time())}_{folder.name}"
            logger.info("Folder name already exists in db. Renaming folder.")

        folder_id = folder_handler.insert_folder(folder)
        folder.folder_id = folder_id

        # Get book info from files in the folder
        books = books_from_folder(folder)

        # Add books to the database
        book_handler = BookDBHandler(con)
        book_handler.insert_books(books)

    return {"success": True, "message": "Folder and books added successfully."}


@app.post("/folders/edit/{folder_id}")
def edit_folder(folder_id: int, folderRB: FolderRequestBody):
    if folderRB.path == "":
        print("bla")
        return {"success": False, "message": "No path provided."}

    if Path(folderRB.path).exists() == False:
        print("ble")
        return {"success": False, "message": "Folder does not exist."}

    content = {
        "name": folderRB.name,
        "path": folderRB.path,
    }

    with DatabaseConnector() as con:
        folder_handler = FolderDBHandler(con)
        if not folder_handler.update_folder(folder_id, content):
            return {"success": False, "message": "The data provided is invalid"}

    return {"success": True}


@app.post("/folders/delete/{folder_id}")
def delete_folder(folder_id: int):
    with DatabaseConnector() as con:
        folder_handler = FolderDBHandler(con)
        if not folder_handler.delete_folder(folder_id):
            return {
                "success": False,
                "message": "Deletion failed. See the logs for more information."
            }

    return {"success": True}
