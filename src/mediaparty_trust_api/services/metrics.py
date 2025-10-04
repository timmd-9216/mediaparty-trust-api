"""Metric calculation functions using Stanza NLP analysis."""

import json
import logging
import os
import re
from typing import List

import dspy
import requests
from stanza import Document

from mediaparty_trust_api.models import Metric

# Configure logger
logger = logging.getLogger(__name__)


class OpenRouterLM(dspy.LM):
    """Custom DSPy LM that uses OpenRouter API directly."""

    def __init__(self, model: str = "google/gemma-2-9b-it:free", **kwargs):
        self.model = model
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        self.kwargs = kwargs
        super().__init__(model=model)

    def __call__(self, prompt=None, messages=None, **kwargs):
        # Prepare messages
        if messages is None:
            messages = [{"role": "user", "content": prompt}]

        logger.info(f"Calling OpenRouter API with model: {self.model}")
        logger.debug(f"Request messages: {messages}")

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.getenv("SITE_URL", ""),
                "X-Title": os.getenv("SITE_NAME", "MediaParty Trust API"),
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.1),
                "top_p": kwargs.get("top_p", 0.9),
                "max_tokens": kwargs.get("max_tokens", 500),
            }
        )

        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                logger.info(f"OpenRouter API call successful. Response length: {len(content)} chars")
                logger.debug(f"Response content: {content}")
                # Return in the format DSPy expects
                return [content]
            else:
                logger.error("No response from model")
                raise ValueError("No response from model")
        else:
            logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
            raise ValueError(f"API error: {response.status_code} - {response.text}")


class QualitativeAdjectiveFilter(dspy.Signature):
    """Filter and count qualitative/calificative adjectives from a list."""

    adjectives: str = dspy.InputField(
        desc="Comma-separated list of adjectives extracted from a news article"
    )
    count: str = dspy.OutputField(
        desc=(
            "Return ONLY the integer number of qualitative/calificative adjectives. "
            "No words, explanations, or units—just the integer as text."
        )
    )


def get_adjective_count(doc: Document, metric_id: int = 1) -> Metric:
    """
    Calculate qualitative adjective ratio metric from Stanza document.

    Analyzes the proportion of qualitative/calificative adjectives in the text.
    Uses DSPy with OpenRouter LM to filter only subjective adjectives that express opinion or judgment.
    A healthy ratio indicates objective writing, while too many qualitative adjectives
    may suggest opinionated or sensationalist content.

    Args:
        doc: Stanza Document object with linguistic annotations
        metric_id: Unique identifier for this metric

    Returns:
        Metric object with qualitative adjective analysis results
    """
    total_words = 0
    adjectives: List[str] = []

    # Iterate through all sentences and words to collect adjectives
    for sentence in doc.sentences:
        for word in sentence.words:
            total_words += 1
            # ADJ is the universal POS tag for adjectives
            if word.upos == "ADJ":
                adjectives.append(word.text)

    # If no adjectives found, return early
    if not adjectives:
        return Metric(
            id=metric_id,
            criteria_name="Qualitative Adjectives",
            explanation="No adjectives found in the text.",
            flag=1,
            score=1.0,
        )

    # Use DSPy with OpenRouter to filter qualitative adjectives
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        # No filtering - use all adjectives if no API key configured
        qualitative_adjective_count = len(adjectives)
        logger.warning("OPENROUTER_API_KEY not set, using all adjectives without filtering")
    else:
        logger.info("Attempting OpenRouter filtering for qualitative adjectives")
        filtered_with_llm = False
        try:
            # Configure DSPy with custom OpenRouter LM inside a context so async tasks don't conflict
            lm = OpenRouterLM(model="google/gemma-2-9b-it:free")
            with dspy.context(lm=lm):
                # Create DSPy module with signature for input/output validation
                filter_module = dspy.ChainOfThought(QualitativeAdjectiveFilter)

                # Call the module with adjectives
                adjectives_str = ", ".join(adjectives)
                logger.info(f"Filtering {len(adjectives)} adjectives with LLM")
                result = filter_module(adjectives=adjectives_str)

                # Extract the count from validated output; tolerate stray characters
                raw_count = str(result.count).strip()
                match = re.search(r"\d+", raw_count)
                if not match:
                    raise ValueError(
                        f"LLM response did not contain an integer count: '{raw_count}'"
                    )

                qualitative_adjective_count = int(match.group())
                filtered_with_llm = True
                logger.info(
                    f"LLM filtered to {qualitative_adjective_count} qualitative adjectives"
                )
        except Exception as e:
            # Failover: if OpenRouter fails, skip filtering and use all adjectives
            logger.error(f"OpenRouter API failed: {e}. Skipping adjective filtering, using all adjectives.")
            qualitative_adjective_count = len(adjectives)
        finally:
            if filtered_with_llm:
                logger.info("OpenRouter filtering succeeded; LLM-provided count will be used")
            else:
                logger.warning(
                    "OpenRouter filtering unavailable, using raw adjective count instead"
                )

    # Calculate ratio using qualitative adjectives only
    adjective_ratio = qualitative_adjective_count / total_words if total_words > 0 else 0

    # Define thresholds for evaluation
    # Typical news articles should have minimal qualitative adjectives (< 5%)
    if adjective_ratio <= 0.05:
        flag = 1
        score = 0.9
        explanation = (
            f"The qualitative adjective ratio ({adjective_ratio:.1%}) is excellent, "
            f"indicating objective writing."
        )
    elif adjective_ratio <= 0.10:
        flag = 0
        score = 0.6
        explanation = (
            f"The qualitative adjective ratio ({adjective_ratio:.1%}) is moderate."
        )
    else:
        flag = -1
        score = 0.3
        explanation = (
            f"The qualitative adjective ratio ({adjective_ratio:.1%}) is too high, "
            f"suggesting opinionated or sensationalist content."
        )

    return Metric(
        id=metric_id,
        criteria_name="Qualitative Adjectives",
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
