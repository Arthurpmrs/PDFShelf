from pathlib import Path
from dataclasses import dataclass
from src.pdfshelf.domain import Folder
from src.pdfshelf.importer import books_from_folder
from src.pdfshelf.config import config_folder
from src.pdfshelf.database import DatabaseConnector, BookDBHandler, FolderDBHandler
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse


@dataclass
class FolderRequestBody:
    name: str
    path: str


app = FastAPI()

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
        return {"success": False, "message": "No path provided."}

    folder_path = Path(folderRB.path)
    if folder_path.exists() == False:
        return {"success": False, "message": "Folder does not exist."}

    folder_name = folderRB.name
    if folderRB.name == "":
        folder_name = folder_path.name

    folder = Folder.from_raw_data({
        "path": folder_path,
        "name": folder_name,
        "active": 1
    })

    # with DatabaseConnector() as con:
    #     folder_handler = FolderDBHandler(con)
    #     folder_handler.insert_folder(folder)

    return {"success": True}


@app.post("/folders/edit/{folder_id}")
def edit_folder(folder_id: int, folderRB: FolderRequestBody):
    print(folder_id, folderRB)
    return {"success": True}
