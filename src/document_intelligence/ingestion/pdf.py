from pathlib import Path
from pypdf import PdfReader


def extract_text(file_path: str | Path) -> str:
    reader = PdfReader(file_path)

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n".join(pages)
