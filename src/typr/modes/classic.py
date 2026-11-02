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

    def as_dict(self):
        return asdict(self)

    def validate(self):
        if type(self.length) is not int:
            raise ValueError("Test length must be a whole number")
        if self.language not in ("en", "de") or self.difficulty not in ("common", "mixed", "advanced"):
            raise ValueError("Unsupported language or difficulty")
        lengths = {"time": (15, 30, 60, 120), "words": (10, 25, 50, 100)}
        if self.test_type not in lengths or self.length not in lengths[self.test_type]:
            raise ValueError("Unsupported test length")


def generate(config, rng=None, count=None):
    config.validate()
    bank = json.loads(files("typr").joinpath(f"assets/words/{config.language}.json").read_text(encoding="utf-8"))
    words = bank[config.difficulty]
    amount = count or (config.length if config.test_type == "words" else 120)
    return " ".join((rng or random).choices(words, k=amount))
