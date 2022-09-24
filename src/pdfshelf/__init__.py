import logging
from logging.handlers import RotatingFileHandler
from .config import config_folder

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
f_format = logging.Formatter('%(asctime)s %(name)-22s %(levelname)-8s [%(lineno)-3s] %(message)s', "%Y-%m-%d %H:%M")
s_format = logging.Formatter('%(name)-22s %(levelname)-8s [%(lineno)-3s] %(message)s')

f_handler = RotatingFileHandler(config_folder / "pdfshelf.log", maxBytes=5000, backupCount=25)
f_handler.setLevel(logging.DEBUG)
f_handler.setFormatter(f_format)

s_handler = logging.StreamHandler()
s_handler.setLevel(logging.WARNING)
s_handler.setFormatter(s_format)

logger.addHandler(f_handler)
logger.addHandler(s_handler)