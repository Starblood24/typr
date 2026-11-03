from dataclasses import asdict, dataclass
from importlib.resources import files
import json
import random


@dataclass
class ClassicConfig:
    language: str = "en"
    difficulty: str = "common"
    test_type: str = "time"
    length: int = 30
    mode: str = "standard"
    code_language: str = "python"

    def as_dict(self):
        return asdict(self)

    def validate(self):
        if self.mode not in ("standard", "developer"):
            raise ValueError("Unsupported content mode")
        if self.code_language not in ("python", "javascript", "typescript", "rust"):
            raise ValueError("Unsupported code language")
        if type(self.length) is not int:
            raise ValueError("Test length must be a whole number")
        if self.language not in ("en", "de") or self.difficulty not in ("common", "mixed", "advanced"):
            raise ValueError("Unsupported language or difficulty")
        lengths = {"time": (15, 30, 60, 120), "words": (10, 25, 50, 100)}
        if self.mode == "developer":
            lengths = {"time": (15, 30, 60, 120), "snippet": (1,)}
        if self.test_type not in lengths or self.length not in lengths[self.test_type]:
            raise ValueError("Unsupported test length")


def generate(config, rng=None, previous=None):
    config.validate()
    if config.mode == "developer":
        from .developer import generate_snippet
        return generate_snippet(config.code_language, rng, previous)
    bank = json.loads(files("typr").joinpath(f"assets/words/{config.language}.json").read_text(encoding="utf-8"))
    words = bank.get(config.difficulty) if isinstance(bank, dict) else None
    if (not isinstance(words, list) or not words
            or any(not isinstance(word, str) or not word or not word.isprintable()
                   or any(ch.isspace() for ch in word) for word in words)):
        raise ValueError(f"Invalid word bank: {config.language}/{config.difficulty}")
    amount = config.length if config.test_type == "words" else 120
    return " ".join((rng or random).choices(words, k=amount))
