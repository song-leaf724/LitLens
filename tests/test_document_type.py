from app.rag.document_type import document_type_detector


def test_detect_classical_poetry() -> None:
    text = "床前明月光\n疑是地上霜\n举头望明月\n低头思故乡"
    result = document_type_detector.detect(text)

    assert result.document_type == "classical_poetry"
    assert result.chunk_strategy == "poetry"
    assert result.confidence >= 0.75


def test_detect_classical_prose() -> None:
    text = "晋太元中，武陵人捕鱼为业。缘溪行，忘路之远近。忽逢桃花林，夹岸数百步，中无杂树，芳草鲜美，落英缤纷。"
    result = document_type_detector.detect(text)

    assert result.document_type == "classical_prose"
    assert result.chunk_strategy == "classical_prose"


def test_detect_english_fiction() -> None:
    text = "It was a bright cold day in April, and the clocks were striking thirteen. The hallway smelt of boiled cabbage and old rag mats."
    result = document_type_detector.detect(text)

    assert result.document_type == "english_fiction"


def test_detect_modern_chinese() -> None:
    text = "夜色降临时，母亲仍坐在窗前等待远行的孩子。这份等待不是简单的牵挂，而像一盏灯。"
    result = document_type_detector.detect(text)

    assert result.document_type == "modern_chinese"


def test_detect_classical_poetry_with_title_and_author() -> None:
    text = "静夜思\n唐  李白\n床前明月光\n疑是地上霜\n举头望明月\n低头思故乡"
    result = document_type_detector.detect(text)

    assert result.document_type == "classical_poetry"
    assert result.chunk_strategy == "poetry"
