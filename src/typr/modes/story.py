from dataclasses import dataclass
from importlib.resources import files
import json


@dataclass(frozen=True)
class Story:
    id: str
    title: str
    language: str
    chapters: list

    @property
    def paragraphs(self):
        return [(c, p, text) for c, chapter in enumerate(self.chapters)
                for p, text in enumerate(chapter["paragraphs"])]


def load_stories():
    stories = []
    root = files("typr").joinpath("assets/stories")
    for language in ("en", "de"):
        for path in sorted(root.joinpath(language).iterdir(), key=lambda p: p.name):
            if path.name.endswith(".json"):
                data = json.loads(path.read_text(encoding="utf-8"))
                story = Story(**data)
                if story.language != language or not story.chapters:
                    raise ValueError(f"Invalid story: {path.name}")
                for chapter in story.chapters:
                    if not chapter.get("title") or not chapter.get("paragraphs"):
                        raise ValueError(f"Empty chapter: {path.name}")
                    if any(not isinstance(p, str) or not p or not p.isprintable() for p in chapter["paragraphs"]):
                        raise ValueError(f"Invalid paragraph: {path.name}")
                if any(s.id == story.id for s in stories):
                    raise ValueError(f"Duplicate story: {story.id}")
                stories.append(story)
    return stories
