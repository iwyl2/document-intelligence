from document_intelligence.processing.document import clean_document
from document_intelligence.models.document import Document, DocumentPage


def test_clean_document_clean_all_pages():
    document = Document(
        file_name="test.pdf",
        pages=[
            DocumentPage(
                page_number=1,
                text="   Hello    World   ",
            ),
            DocumentPage(
                page_number=2,
                text="   This    is    page two   ",
            ),
        ],
    )

    result = clean_document(document=document)

    assert result.pages[0].text == "Hello World"
    assert result.pages[1].text == "This is page two"
