import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOOKS_DIR = os.path.join(BASE_DIR, "files")
TEMP_DIR = os.path.join(BASE_DIR, "local_file_storage")
DB_DIR = os.path.join(BASE_DIR, "db")
DB_PATH = os.path.join(DB_DIR, "knigniypomoschnik.db")


def ensure_dirs():
    for directory in (BOOKS_DIR, TEMP_DIR, DB_DIR):
        os.makedirs(directory, exist_ok=True)


def resolve_book_path(stored_path):
    name = os.path.basename(stored_path.replace("\\", "/"))
    return os.path.join(BOOKS_DIR, name)


def clean_filename(name):
    return re.sub(r'[\\/:*?"<>|\r\n\t]', "", name).strip()
