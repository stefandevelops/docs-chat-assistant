from docs_chat.textutil import candidate_sentences, split_sentences, tokenize


def test_tokenize_drops_stopwords_and_stems() -> None:
    tokens = tokenize("How many days do customers have to return a bike?")
    assert "how" not in tokens
    assert "day" in tokens or "days" in tokens
    assert "customer" in tokens
    assert "return" in tokens


def test_split_sentences_keeps_policy_lines() -> None:
    text = (
        "Customers have 30 days from the delivery date to start a return. "
        "The customer pays return shipping on change-of-mind returns."
    )
    sentences = split_sentences(text)
    assert len(sentences) == 2
    assert "30 days" in sentences[0]


def test_candidate_sentences_skip_tables() -> None:
    text = (
        "| Battery | 2 years or 600 charge cycles |\n"
        "The battery warranty is 2 years or 600 charge cycles, whichever comes first."
    )
    sentences = candidate_sentences(text)
    assert all("|" not in sentence for sentence in sentences)
    assert any("battery warranty is 2 years" in sentence.lower() for sentence in sentences)
