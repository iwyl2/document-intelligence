from document_intelligence.processing.text import clean_text


def test_clean_text_remove_extra_spaces():
    text = "Students  must        attend"

    result = clean_text(text)

    assert result == "Students must attend"


def test_clean_text_normalize_line_endings():
    text = "Hello\r\nWorld"

    result = clean_text(text)

    assert result == "Hello\nWorld"


def test_clean_text_removes_line_whitespace():
    text = "   Hello   \n   World   "

    result = clean_text(text)

    assert result == "Hello\nWorld"


def test_clean_text_preserves_paragraphs():
    text = "Hello\n\nWorld"

    result = clean_text(text)

    assert result == "Hello\n\nWorld"
