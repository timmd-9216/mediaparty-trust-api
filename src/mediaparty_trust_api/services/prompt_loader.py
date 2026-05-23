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
