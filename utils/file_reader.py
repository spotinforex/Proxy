import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)

def read_file(file_path: str) -> str:
    """Read the contents of a file and return it as a string."""
    path = f"{Path.cwd()}\{file_path}"
    logging.info(f"Reading file: {path}")
    if not Path(path).is_file():
        raise FileNotFoundError(f"File not found: {file_path}")
    return Path(path).read_text(encoding="utf-8")