from pathlib import Path
from src.pdfshelf.importer import books_from_folder
from src.pdfshelf.config import config_folder
from src.pdfshelf.database import DatabaseConnector, BookDBHandler, FolderDBHandler
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI()

templates = Jinja2Templates(directory="src/templates")
app.mount("/static", StaticFiles(directory="src/static"), name="static")


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
