"""Metric calculation functions using Stanza NLP analysis."""

import json
import logging
import os
import re
from typing import List, Optional

import dspy
import requests

try:
    from stanza import Document
except ImportError:
    Document = None  # type: ignore

from mediaparty_trust_api.models import Metric
from mediaparty_trust_api.services.prompt_loader import load_dspy_signature, load_thresholds

# Configure logger
logger = logging.getLogger(__name__)


class OpenRouterLM(dspy.LM):
    """Custom DSPy LM that uses OpenRouter API directly."""

    DEFAULT_MODEL = "google/gemma-4-31b-it:free"

    def __init__(self, model: str | None = None, **kwargs):
        self.model = model or os.getenv("OPENROUTER_MODEL", self.DEFAULT_MODEL)
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        self.kwargs = kwargs
        super().__init__(model=self.model)

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
                logger.info(
                    f"OpenRouter API call successful (model={self.model}, "
                    f"response length={len(content)} chars)"
                )
                logger.info(f"Raw LLM response: {content!r}")
                # Return in the format DSPy expects
                return [content]
            else:
                logger.error("No response from model")
                raise ValueError("No response from model")
        else:
            logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
            raise ValueError(f"API error: {response.status_code} - {response.text}")


# Signature loaded from versioned prompt files at `prompts/prompt-adjectives.{txt,json}`.
# The .txt file contains the instructions (optimizable by DSPy); the .json file
# defines the structured input/output schema.
QualitativeAdjectiveFilter = load_dspy_signature("adjectives")


def get_adjective_count(text: str, metric_id: int = 1, doc: Optional[object] = None) -> Metric:
    """
    Calculate qualitative adjective ratio metric.

    When a Stanza Document is provided, uses POS-tagged adjectives for precision.
    Otherwise, delegates directly to the LLM to identify qualitative adjectives
    from the raw text, without a pre-filtered list.

    Args:
        text: Raw article text (always required)
        metric_id: Unique identifier for this metric
        doc: Optional Stanza Document; when present adjectives are POS-extracted first

    Returns:
        Metric object with qualitative adjective analysis results
    """
    total_words = 0
    adjectives: List[str] = []

    if doc is not None:
        # Precise path: extract adjectives via POS tags
        for sentence in doc.sentences:
            for word in sentence.words:
                total_words += 1
                if word.upos == "ADJ":
                    adjectives.append(word.text)
    else:
        # Fallback: count words from plain text; adjective list left empty
        # (LLM will work on the full text string instead)
        total_words = len(text.split())

    # If no adjectives found (and we have a doc), return early
    if doc is not None and not adjectives:
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
        qualitative_adjective_count = len(adjectives) if adjectives else 0
        logger.warning("OPENROUTER_API_KEY not set, using all adjectives without filtering")
    else:
        logger.info("Attempting OpenRouter filtering for qualitative adjectives")
        filtered_with_llm = False
        try:
            # Configure DSPy with custom OpenRouter LM inside a context so async tasks don't conflict
            # Model is configurable via OPENROUTER_MODEL env var
            lm = OpenRouterLM()
            with dspy.context(lm=lm):
                # Create DSPy module with signature for input/output validation
                filter_module = dspy.ChainOfThought(QualitativeAdjectiveFilter)

                # If we have a POS-extracted list use it; otherwise pass the full text
                adjectives_str = ", ".join(adjectives) if adjectives else text
                logger.info(f"Filtering {'adjectives list' if adjectives else 'full text'} with LLM")
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
    _total = total_words if total_words > 0 else len(text.split()) or 1
    adjective_ratio = qualitative_adjective_count / _total

    # Load thresholds from prompt JSON
    th = load_thresholds("adjectives")
    excellent_max = th.get("excellent", {}).get("max_ratio", 0.05)
    moderate_max = th.get("moderate", {}).get("max_ratio", 0.10)

    if adjective_ratio <= excellent_max:
        flag = th.get("excellent", {}).get("flag", 1)
        score = th.get("excellent", {}).get("score", 0.9)
        explanation = (
            f"The qualitative adjective ratio ({adjective_ratio:.1%}) is excellent, "
            f"indicating objective writing."
        )
    elif adjective_ratio <= moderate_max:
        flag = th.get("moderate", {}).get("flag", 0)
        score = th.get("moderate", {}).get("score", 0.6)
        explanation = (
            f"The qualitative adjective ratio ({adjective_ratio:.1%}) is moderate."
        )
    else:
        flag = th.get("high", {}).get("flag", -1)
        score = th.get("high", {}).get("score", 0.3)
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


def get_word_count(text: str, metric_id: int = 2, doc: Optional[object] = None) -> Metric:
    """
    Calculate total word count metric.

    Uses Stanza token counts when a Document is available; falls back to
    simple whitespace splitting on plain text.

    Args:
        text: Raw article text (always required)
        metric_id: Unique identifier for this metric
        doc: Optional Stanza Document for precise tokenisation

    Returns:
        Metric object with word count analysis results
    """
    if doc is not None:
        total_words = sum(len(sentence.words) for sentence in doc.sentences)
    else:
        total_words = len(text.split())

    # Load thresholds from prompt JSON
    th = load_thresholds("word-count")
    comprehensive = th.get("comprehensive", {})
    adequate = th.get("adequate", {})
    too_brief = th.get("too_brief", {})

    if total_words >= comprehensive.get("min_words", 500):
        flag = comprehensive.get("flag", 1)
        score = comprehensive.get("score", 0.9)
        explanation = (
            f"The article has {total_words} words, indicating comprehensive coverage."
        )
    elif total_words >= adequate.get("min_words", 300):
        flag = adequate.get("flag", 0)
        score = adequate.get("score", 0.6)
        explanation = f"The article has {total_words} words, which is adequate."
    else:
        flag = too_brief.get("flag", -1)
        score = too_brief.get("score", 0.3)
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


def get_sentence_complexity(text: str, metric_id: int = 3, doc: Optional[object] = None) -> Metric:
    """
    Calculate average sentence length metric.

    Uses Stanza sentence/token counts when a Document is available; falls back
    to regex sentence splitting and whitespace word counting on plain text.

    Args:
        text: Raw article text (always required)
        metric_id: Unique identifier for this metric
        doc: Optional Stanza Document for precise tokenisation

    Returns:
        Metric object with sentence complexity analysis results
    """
    if doc is not None:
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
    else:
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        sentence_count = len(sentences)
        if sentence_count == 0:
            return Metric(
                id=metric_id,
                criteria_name="Sentence Complexity",
                explanation="No sentences found in the text.",
                flag=-1,
                score=0.0,
            )
        total_words = sum(len(s.split()) for s in sentences)
    avg_sentence_length = total_words / sentence_count

    # Load thresholds from prompt JSON
    th = load_thresholds("sentence-complexity")
    optimal = th.get("optimal", {})
    acceptable_low = th.get("acceptable_low", {})
    acceptable_high = th.get("acceptable_high", {})
    too_short = th.get("too_short", {})
    too_long = th.get("too_long", {})

    opt_min, opt_max = optimal.get("min", 15), optimal.get("max", 25)
    acc_low_min, acc_low_max = acceptable_low.get("min", 10), acceptable_low.get("max", 15)
    acc_high_min, acc_high_max = acceptable_high.get("min", 25), acceptable_high.get("max", 35)
    short_max = too_short.get("max", 10)
    long_min = too_long.get("min", 35)

    if opt_min <= avg_sentence_length <= opt_max:
        flag = optimal.get("flag", 1)
        score = optimal.get("score", 0.9)
        explanation = f"Average sentence length ({avg_sentence_length:.1f} words) is optimal for readability."
    elif acc_low_min <= avg_sentence_length < acc_low_max or acc_high_min < avg_sentence_length <= acc_high_max:
        flag = acceptable_low.get("flag", 0)
        score = acceptable_low.get("score", 0.6)
        explanation = (
            f"Average sentence length ({avg_sentence_length:.1f} words) is acceptable."
        )
    else:
        flag = too_short.get("flag", -1)
        score = too_short.get("score", 0.3)
        if avg_sentence_length < short_max:
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


def get_verb_tense_analysis(text: str, metric_id: int = 4, doc: Optional[object] = None) -> Metric:
    """
    Analyze verb tense distribution in the document.

    Requires a Stanza Document for POS/feature analysis. When unavailable,
    returns a metric indicating the NLP service is offline.

    Args:
        text: Raw article text (always required)
        metric_id: Unique identifier for this metric
        doc: Optional Stanza Document; metric is N/A without it

    Returns:
        Metric object with verb tense analysis results
    """
    if doc is None:
        return Metric(
            id=metric_id,
            criteria_name="Verb Tense",
            explanation="Verb tense analysis requires the NLP service (Stanza). Currently unavailable.",
            flag=0,
            score=0.0,
        )

    verb_count = 0
    past_tense_count = 0

    for sentence in doc.sentences:
        for word in sentence.words:
            if word.upos == "VERB":
                verb_count += 1
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

    # Load thresholds from prompt JSON
    th = load_thresholds("verb-tense")
    appropriate = th.get("appropriate", {})
    acceptable_low = th.get("acceptable_low", {})
    acceptable_high = th.get("acceptable_high", {})
    unusual_low = th.get("unusual_low", {})
    unusual_high = th.get("unusual_high", {})

    app_min, app_max = appropriate.get("min_ratio", 0.4), appropriate.get("max_ratio", 0.7)
    acc_low_min, acc_low_max = acceptable_low.get("min_ratio", 0.2), acceptable_low.get("max_ratio", 0.4)
    acc_high_min, acc_high_max = acceptable_high.get("min_ratio", 0.7), acceptable_high.get("max_ratio", 0.85)
    un_low_max = unusual_low.get("max_ratio", 0.2)
    un_high_min = unusual_high.get("min_ratio", 0.85)

    if app_min <= past_tense_ratio <= app_max:
        flag = appropriate.get("flag", 1)
        score = appropriate.get("score", 0.85)
        explanation = f"Past tense usage ({past_tense_ratio:.1%}) suggests appropriate news reporting style."
    elif acc_low_min <= past_tense_ratio < acc_low_max or acc_high_min < past_tense_ratio <= acc_high_max:
        flag = acceptable_low.get("flag", 0)
        score = acceptable_low.get("score", 0.6)
        explanation = f"Past tense usage ({past_tense_ratio:.1%}) is acceptable but could be more balanced."
    else:
        flag = unusual_low.get("flag", -1)
        score = unusual_low.get("score", 0.3)
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
