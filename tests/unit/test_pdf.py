from pathlib import Path
from document_intelligence.ingestion.pdf import extract_document

FIXTURES_DIR = Path("tests/fixtures/documents")


def test_extract_text_from_pdf():
    pdf_path = FIXTURES_DIR / "simple_text.pdf"

    document = extract_document(pdf_path)

    assert document.file_name == "simple_text.pdf"
    assert len(document.pages) == 1

    page = document.pages[0]

    assert page.page_number == 1
    assert "Academic Guidelines" in page.text
    assert "40 marks" in page.text
    assert "80%" in page.text


def test_extract_text_from_multipage_pdf():
    pdf_path = FIXTURES_DIR / "multipage_academic.pdf"

    document = extract_document(pdf_path)

    assert document.file_name == "multipage_academic.pdf"
    assert len(document.pages) == 3

    assert document.pages[0].page_number == 1
    assert document.pages[1].page_number == 2
    assert document.pages[2].page_number == 3

    assert "Chapter 1 - Attendance" in document.pages[0].text
    assert "Chapter 2 - Examinations" in document.pages[1].text
    assert "Chapter 3 - Assignments" in document.pages[2].text


def test_extract_document_from_table_pdf():
    pdf_path = FIXTURES_DIR / "academic_table.pdf"

    document = extract_document(pdf_path)

    assert document.file_name == "academic_table.pdf"
    assert len(document.pages) == 1

    text = document.pages[0].text

    assert "Module Requirements" in text
    assert "Applied Mathematics" in text
    assert "40" in text
    assert "80%" in text
