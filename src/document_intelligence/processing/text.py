import re
import unicodedata


def clean_text(text: str) -> str:
    """
    Normalize extracted PDF text while preserving paragraph structure.
    """

    text = text.replace("\r\n", "\n").replace("\r", "\n")

    text = unicodedata.normalize("NFKC", text)

    text = text.strip()

    lines = [line.strip() for line in text.split("\n")]
    lines = [re.sub(r"[ \t]+", " ", line) for line in lines]

    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()