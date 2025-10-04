"""Metric calculation functions using Stanza NLP analysis."""

from stanza import Document

from mediaparty_trust_api.models import Metric


def get_adjective_count(doc: Document, metric_id: int = 1) -> Metric:
    """
    Calculate adjective ratio metric from Stanza document.

    Analyzes the proportion of adjectives in the text. A healthy ratio
    indicates objective writing, while too many adjectives may suggest
    opinionated or sensationalist content.

    Args:
        doc: Stanza Document object with linguistic annotations
        metric_id: Unique identifier for this metric

    Returns:
        Metric object with adjective analysis results
    """
    total_words = 0
    adjective_count = 0

    # Iterate through all sentences and words
    for sentence in doc.sentences:
        for word in sentence.words:
            total_words += 1
            # ADJ is the universal POS tag for adjectives
            if word.upos == "ADJ":
                adjective_count += 1

    # Calculate ratio
    adjective_ratio = adjective_count / total_words if total_words > 0 else 0

    # Define thresholds for evaluation
    # Typical news articles have 5-10% adjectives
    if adjective_ratio <= 0.12:
        flag = 1
        score = 0.9
        explanation = (
            f"The adjective ratio ({adjective_ratio:.1%}) is good and healthy."
        )
    elif adjective_ratio <= 0.20:
        flag = 0
        score = 0.6
        explanation = f"The adjective ratio ({adjective_ratio:.1%}) is moderate."
    else:
        flag = -1
        score = 0.3
        explanation = f"The adjective ratio ({adjective_ratio:.1%}) is too high, suggesting opinionated content."

    return Metric(
        id=metric_id,
        criteria_name="Adjectives",
        explanation=explanation,
        flag=flag,
        score=score,
    )


def get_word_count(doc: Document, metric_id: int = 2) -> Metric:
    """
    Calculate total word count metric from Stanza document.

    Analyzes the length of the text. Longer articles tend to be more
    comprehensive and well-researched.

    Args:
        doc: Stanza Document object with linguistic annotations
        metric_id: Unique identifier for this metric

    Returns:
        Metric object with word count analysis results
    """
    total_words = sum(len(sentence.words) for sentence in doc.sentences)

    # Define thresholds
    if total_words >= 500:
        flag = 1
        score = 0.9
        explanation = (
            f"The article has {total_words} words, indicating comprehensive coverage."
        )
    elif total_words >= 300:
        flag = 0
        score = 0.6
        explanation = f"The article has {total_words} words, which is adequate."
    else:
        flag = -1
        score = 0.3
        explanation = (
            f"The article has only {total_words} words, which may be too brief."
        )

    return Metric(
        id=metric_id,
        criteria_name="Word Count",
        explanation=explanation,
        flag=flag,
        score=score,
    )


def get_sentence_complexity(doc: Document, metric_id: int = 3) -> Metric:
    """
    Calculate average sentence length metric from Stanza document.

    Analyzes sentence complexity through average word count per sentence.
    Moderate sentence length indicates readable and well-structured writing.

    Args:
        doc: Stanza Document object with linguistic annotations
        metric_id: Unique identifier for this metric

    Returns:
        Metric object with sentence complexity analysis results
    """
    sentence_count = len(doc.sentences)

    if sentence_count == 0:
        return Metric(
            id=metric_id,
            criteria_name="Sentence Complexity",
            explanation="No sentences found in the text.",
            flag=-1,
            score=0.0,
        )

    total_words = sum(len(sentence.words) for sentence in doc.sentences)
    avg_sentence_length = total_words / sentence_count

    # Define thresholds (ideal range: 15-25 words per sentence)
    if 15 <= avg_sentence_length <= 25:
        flag = 1
        score = 0.9
        explanation = f"Average sentence length ({avg_sentence_length:.1f} words) is optimal for readability."
    elif 10 <= avg_sentence_length < 15 or 25 < avg_sentence_length <= 35:
        flag = 0
        score = 0.6
        explanation = (
            f"Average sentence length ({avg_sentence_length:.1f} words) is acceptable."
        )
    else:
        flag = -1
        score = 0.3
        if avg_sentence_length < 10:
            explanation = f"Sentences are too short ({avg_sentence_length:.1f} words on average), suggesting oversimplification."
        else:
            explanation = f"Sentences are too long ({avg_sentence_length:.1f} words on average), which may affect readability."

    return Metric(
        id=metric_id,
        criteria_name="Sentence Complexity",
        explanation=explanation,
        flag=flag,
        score=score,
    )


def get_verb_tense_analysis(doc: Document, metric_id: int = 4) -> Metric:
    """
    Analyze verb tense distribution in the document.

    News articles typically use past tense for reporting events.
    A healthy distribution suggests objective reporting.

    Args:
        doc: Stanza Document object with linguistic annotations
        metric_id: Unique identifier for this metric

    Returns:
        Metric object with verb tense analysis results
    """
    verb_count = 0
    past_tense_count = 0

    for sentence in doc.sentences:
        for word in sentence.words:
            # VERB is the universal POS tag for verbs
            if word.upos == "VERB":
                verb_count += 1
                # Check if verb is in past tense
                if word.feats and "Tense=Past" in word.feats:
                    past_tense_count += 1

    if verb_count == 0:
        return Metric(
            id=metric_id,
            criteria_name="Verb Tense",
            explanation="No verbs found in the text.",
            flag=-1,
            score=0.0,
        )

    past_tense_ratio = past_tense_count / verb_count

    # News articles typically have 40-70% past tense verbs
    if 0.4 <= past_tense_ratio <= 0.7:
        flag = 1
        score = 0.85
        explanation = f"Past tense usage ({past_tense_ratio:.1%}) suggests appropriate news reporting style."
    elif 0.2 <= past_tense_ratio < 0.4 or 0.7 < past_tense_ratio <= 0.85:
        flag = 0
        score = 0.6
        explanation = f"Past tense usage ({past_tense_ratio:.1%}) is acceptable but could be more balanced."
    else:
        flag = -1
        score = 0.3
        explanation = (
            f"Past tense usage ({past_tense_ratio:.1%}) is unusual for news reporting."
        )

    return Metric(
        id=metric_id,
        criteria_name="Verb Tense",
        explanation=explanation,
        flag=flag,
        score=score,
    )
