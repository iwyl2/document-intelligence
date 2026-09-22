from pathlib import Path
from document_intelligence.ingestion.pdf import extract_text

FIXTURES_DIR = Path("tests/fixtures/documents")


def test_extract_text_from_pdf():
    pdf_path = FIXTURES_DIR / "simple_text.pdf"

    text = extract_text(pdf_path)

    assert "Academic Guidelines" in text
    assert "40 marks" in text
    assert "80%" in text
    assert "Assignments" in text


def test_extract_text_from_multipage_pdf():
    pdf_path = FIXTURES_DIR / "multipage_academic.pdf"

    text = extract_text(pdf_path)

    assert "Chapter 1 - Attendance" in text
    assert "Chapter 2 - Examinations" in text
    assert "Chapter 3 - Assignments" in text


def test_extract_text_from_scanned_pdf():
    pdf_path = FIXTURES_DIR / "scanned_document.pdf"

    text = extract_text(pdf_path)

    print(repr(text))


def test_extract_text_from_empty_pdf():
    pdf_path = FIXTURES_DIR / "empty_document.pdf"

    text = extract_text(pdf_path)

    print(f"Empty PDF: {repr(text)}")


def test_extract_text_from_table_pdf():
    pdf_path = FIXTURES_DIR / "academic_table.pdf"

    text = extract_text(pdf_path)

    print("TABLE PDF:", repr(text))
