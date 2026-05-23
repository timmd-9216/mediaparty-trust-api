"""Load DSPy signatures from versioned prompt files in the `prompts/` directory.

Each prompt is described by two sibling files:

- ``prompt-<name>.txt``  -> Free-text instructions (the signature docstring).
                           This is the artifact that can be versioned and
                           later optimized by DSPy.
- ``prompt-<name>.json`` -> Structured I/O definition with fields:

      {
        "name": "SignatureClassName",
        "inputs":  { "<field>": {"type": "string", "description": "..."} },
        "outputs": { "<field>": {"type": "string", "description": "..."} }
      }

The :func:`load_dspy_signature` function reads both files and builds a
``dspy.Signature`` subclass dynamically (equivalent to declaring the class
by hand with ``dspy.InputField`` / ``dspy.OutputField``).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Type

import dspy

logger = logging.getLogger(__name__)

# Repository-level `prompts/` directory: <repo>/prompts
# This file lives at <repo>/src/mediaparty_trust_api/services/prompt_loader.py
PROMPTS_DIR = Path(__file__).resolve().parents[3] / "prompts"


_TYPE_MAP = {
    "string": str,
    "str": str,
    "integer": int,
    "int": int,
    "number": float,
    "float": float,
    "boolean": bool,
    "bool": bool,
}


def _resolve_type(type_name: str) -> type:
    try:
        return _TYPE_MAP[type_name.lower()]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported prompt field type '{type_name}'. "
            f"Expected one of: {sorted(_TYPE_MAP)}"
        ) from exc


def load_dspy_signature(name: str) -> Type[dspy.Signature]:
    """Build a ``dspy.Signature`` class from ``prompt-<name>.{txt,json}``.

    Args:
        name: Metric short name (e.g. ``"adjectives"``).

    Returns:
        A dynamically created ``dspy.Signature`` subclass equivalent to the
        hand-written class, but with its instructions and field descriptions
        sourced from the prompt files.
    """
    txt_path = PROMPTS_DIR / f"prompt-{name}.txt"
    json_path = PROMPTS_DIR / f"prompt-{name}.json"

    if not txt_path.is_file():
        raise FileNotFoundError(f"Prompt text file not found: {txt_path}")
    if not json_path.is_file():
        raise FileNotFoundError(f"Prompt schema file not found: {json_path}")

    instructions = txt_path.read_text(encoding="utf-8").strip()
    schema = json.loads(json_path.read_text(encoding="utf-8"))

    class_name = schema.get("name") or f"{name.capitalize()}Signature"
    inputs = schema.get("inputs", {}) or {}
    outputs = schema.get("outputs", {}) or {}

    if not inputs:
        raise ValueError(f"Prompt '{name}' must define at least one input field")
    if not outputs:
        raise ValueError(f"Prompt '{name}' must define at least one output field")

    attrs: dict = {"__doc__": instructions, "__annotations__": {}}

    for field_name, spec in inputs.items():
        py_type = _resolve_type(spec.get("type", "string"))
        attrs["__annotations__"][field_name] = py_type
        attrs[field_name] = dspy.InputField(desc=spec.get("description", ""))

    for field_name, spec in outputs.items():
        py_type = _resolve_type(spec.get("type", "string"))
        attrs["__annotations__"][field_name] = py_type
        attrs[field_name] = dspy.OutputField(desc=spec.get("description", ""))

    signature_cls = type(class_name, (dspy.Signature,), attrs)
    logger.debug(
        "Loaded DSPy signature '%s' from %s + %s", class_name, txt_path.name, json_path.name
    )
    return signature_cls


def list_prompts() -> list[dict]:
    """List all prompt definitions available under ``prompts/``.

    Each entry is a dict with ``name`` (short id), ``signature`` (class name
    declared in the JSON), ``has_thresholds`` and ``has_llm_signature`` flags.
    A prompt is considered LLM-driven when its JSON declares both ``inputs``
    and ``outputs``.
    """
    prompts: list[dict] = []
    if not PROMPTS_DIR.is_dir():
        return prompts

    for json_path in sorted(PROMPTS_DIR.glob("prompt-*.json")):
        name = json_path.stem.removeprefix("prompt-")
        try:
            schema = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("Skipping malformed prompt schema %s: %s", json_path.name, e)
            continue
        prompts.append({
            "name": name,
            "signature": schema.get("name", ""),
            "has_thresholds": bool(schema.get("thresholds")),
            "has_llm_signature": bool(schema.get("inputs") and schema.get("outputs")),
        })
    return prompts


def validate_prompts() -> dict:
    """Validate every ``prompt-*.json`` (and its sibling ``.txt``) under ``prompts/``.

    Performs the following checks per prompt:

    - ``.json`` parses as valid JSON
    - ``name`` is present
    - If ``inputs``/``outputs`` are declared, every field has a supported ``type``
    - The matching ``.txt`` exists and is non-empty
    - If the prompt is LLM-driven (has both ``inputs`` and ``outputs``), the
      DSPy signature can actually be built via :func:`load_dspy_signature`
    - Threshold bands, if present, are dicts

    Returns:
        Dict with ``valid`` (list of names), ``errors`` (list of {name, error})
        and ``total`` count.
    """
    valid: list[str] = []
    errors: list[dict] = []
    skipped: list[dict] = []

    if not PROMPTS_DIR.is_dir():
        return {"valid": valid, "errors": errors, "skipped": skipped, "total": 0}

    json_paths = sorted(PROMPTS_DIR.glob("prompt-*.json"))
    for json_path in json_paths:
        name = json_path.stem.removeprefix("prompt-")
        txt_path = PROMPTS_DIR / f"prompt-{name}.txt"
        try:
            schema = json.loads(json_path.read_text(encoding="utf-8"))

            # Files that don't follow our convention (no name AND no recognizable
            # fields) are treated as drafts and skipped rather than failed.
            recognizable = any(
                k in schema for k in ("name", "inputs", "outputs", "thresholds")
            )
            if not recognizable:
                skipped.append({"name": name, "reason": "non-standard schema (draft)"})
                continue

            if not schema.get("name"):
                raise ValueError("missing 'name' in JSON schema")

            inputs = schema.get("inputs") or {}
            outputs = schema.get("outputs") or {}

            for field_name, spec in {**inputs, **outputs}.items():
                type_name = (spec or {}).get("type", "string")
                if type_name.lower() not in _TYPE_MAP:
                    raise ValueError(
                        f"unsupported type '{type_name}' on field '{field_name}'"
                    )

            if not txt_path.is_file():
                raise FileNotFoundError(f"missing sibling text file {txt_path.name}")
            if not txt_path.read_text(encoding="utf-8").strip():
                raise ValueError(f"text file {txt_path.name} is empty")

            thresholds = schema.get("thresholds")
            if thresholds is not None and not isinstance(thresholds, dict):
                raise ValueError("'thresholds' must be a JSON object")

            # If both inputs and outputs are present we treat it as LLM-driven
            # and try to build the DSPy signature to catch any structural errors.
            if inputs and outputs:
                load_dspy_signature(name)

            valid.append(name)
        except Exception as e:
            errors.append({"name": name, "error": str(e)})

    return {
        "valid": valid,
        "errors": errors,
        "skipped": skipped,
        "total": len(json_paths),
    }


def load_thresholds(name: str) -> dict:
    """Load thresholds definition from ``prompt-<name>.json``.

    Args:
        name: Metric short name (e.g. ``"word-count"``).

    Returns:
        Dict with the ``thresholds`` key from the JSON schema, or empty dict
        if the metric has no thresholds defined.

    Raises:
        FileNotFoundError: If the JSON file does not exist.
    """
    json_path = PROMPTS_DIR / f"prompt-{name}.json"

    if not json_path.is_file():
        raise FileNotFoundError(f"Prompt schema file not found: {json_path}")

    schema = json.loads(json_path.read_text(encoding="utf-8"))
    thresholds = schema.get("thresholds", {})
    logger.debug("Loaded thresholds for '%s' from %s", name, json_path.name)
    return thresholds
