"""Bundled typing material. Snippets are displayed as text and never executed."""
from importlib.resources import files
import json
import random


def generate_snippet(language, rng=None, previous=None):
    bank = json.loads(files("typr").joinpath("assets/code/snippets.json").read_text(encoding="utf-8"))
    snippets = bank.get(language) if isinstance(bank, dict) else None
    if (not isinstance(snippets, list) or not snippets
            or any(not isinstance(text, str) or not text.strip()
                   or any(not (ch.isprintable() or ch == "\n") for ch in text) for text in snippets)):
        raise ValueError(f"Invalid code snippets: {language}")
    candidates = [text for text in snippets if text != previous]
    return (rng or random).choice(candidates or snippets)
