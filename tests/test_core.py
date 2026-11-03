import random
from pathlib import Path

import pytest

from typr.core.typing_engine import Session, SessionStatus
from typr.modes.classic import ClassicConfig, generate
from typr.modes.story import load_stories
from typr.storage.database import Database
from typr.ui.widgets import art, progress, wpm_chart


class Clock:
    now = 0.0

    def __call__(self):
        return self.now


def test_timing_starts_at_first_input_and_pause_keeps_running():
    clock = Clock()
    s = Session("abc", duration=15, clock=clock)
    clock.now = 100
    s.tick()
    assert s.elapsed == 0
    s.type("a")
    s.pause_menu()
    s.type("b")
    assert s.typed == "a"
    clock.now = 120
    s.tick()
    assert s.status is SessionStatus.FINISHED
    assert s.elapsed == 15
    assert s.wpm == pytest.approx(.8)
    assert all(t <= 15 for t, _ in s.samples)


def test_standard_errors_unicode_backspace_and_metrics():
    clock = Clock()
    s = Session("für dich", None, clock=clock)
    for ch in "für x":
        s.type(ch)
    s.backspace()
    s.backspace()
    assert s.typed == "für"
    for ch in " dich":
        s.type(ch)
    clock.now = 12
    s.finish()
    assert s.complete
    assert s.wpm == 8
    assert s.accuracy == 90


def test_chart_samples_do_not_include_near_zero_startup_spike():
    clock = Clock()
    session = Session("abcde", None, clock=clock)
    session.type("a")
    clock.now = .00001
    session.tick()
    assert not session.samples
    for time, character in ((.4, "b"), (.8, "c"), (1.2, "d"), (1.6, "e")):
        clock.now = time
        session.type(character)
    clock.now = 2
    session.finish()
    assert session.wpm == 30
    assert [time for time, _ in session.samples] == [1.2, 2]
    assert all(wpm == pytest.approx(30) for _, wpm in session.samples)


def test_subsecond_session_has_no_unreliable_chart_point():
    clock = Clock()
    session = Session("ab", None, clock=clock)
    session.type("a")
    clock.now = .2
    session.type("b")
    session.finish()
    assert not session.samples
    assert "no samples" in wpm_chart(session.samples)


def test_final_sample_replaces_same_timestamp_after_last_character():
    clock = Clock()
    session = Session("ab", None, clock=clock)
    session.type("a")
    clock.now = 1
    session.type("b")
    session.finish()
    assert session.samples == [(1, 24)]


def test_story_strict_correction_and_locked_paragraphs():
    s = Session("ab", None, strict=True)
    s.type("x")
    s.type("a")
    assert s.typed == "x"
    with pytest.raises(ValueError):
        s.next_paragraph("cd")
    s.backspace()
    s.type("a")
    s.type("b")
    s.next_paragraph("cd")
    s.backspace()
    assert s.typed == ""
    assert s.completed_chars == 2
    assert s.attempts == 3


@pytest.mark.parametrize("language", ["en", "de"])
@pytest.mark.parametrize("difficulty", ["common", "mixed", "advanced"])
@pytest.mark.parametrize("kind,length", [("time",15),("time",30),("time",60),("time",120),
                                          ("words",10),("words",25),("words",50),("words",100)])
def test_all_content_configs(language, difficulty, kind, length):
    config = ClassicConfig(language, difficulty, kind, length)
    text = generate(config, random.Random(2))
    assert len(text.split()) == (length if kind == "words" else 120)
    assert text.isprintable()


def test_invalid_config_rejected():
    with pytest.raises(ValueError):
        generate(ClassicConfig(language="../../private"))
    with pytest.raises(ValueError):
        generate(ClassicConfig(length=2))


def test_database_persistence_stats_checkpoint_restart_reset(tmp_path):
    path = tmp_path / "typr.db"
    db = Database(path)
    s = Session("ab", None)
    with pytest.raises(ValueError):
        db.save_session(ClassicConfig(), s)
    s.type("a")
    s.type("b")
    s.finish()
    db.save_session(ClassicConfig(), s)
    db.setting("ascii art", "off")
    db.checkpoint("one", 3)
    db.checkpoint("one", 1)
    db.close()
    db = Database(path)
    assert db.progress("one") == 3
    assert db.settings()["ascii art"] == "off"
    assert db.stats()[0]["total"] == 1
    db.restart_story("one")
    assert db.progress("one") == 0
    db.reset()
    assert db.stats()[0]["total"] == 0
    assert db.settings()["ascii art"] == "on"
    db.close()


def test_assets_and_complete_stories():
    import hashlib
    star = art("staros_star")
    assert len(star.splitlines()) == 24
    assert hashlib.sha256(star.encode()).hexdigest() == "1264138360dc75c1f249add9e9a2a1ca95ee1170a62c100fee6a6376ced5871d"
    stories = load_stories()
    assert len(stories) == 3
    assert {s.language for s in stories} == {"de", "en"}
    illustrations = []
    for s in stories:
        for c in s.chapters:
            for p in c["paragraphs"]:
                assert 40 <= len(p.split()) <= 80
            if c.get("art"):
                assert 6 <= len(c["art"].splitlines()) <= 10
                illustrations.append(c["art"])
    assert len(illustrations) == len(set(illustrations))


def test_chart_and_progress_boundaries():
    assert progress(2).endswith("100%")
    assert progress(-1).endswith("0%")
    chart = wpm_chart([(0, 0), (1, 30), (2, 60)])
    assert "WPM OVER TIME" in chart and "60" in chart and "2s" in chart


@pytest.mark.parametrize("peak", [30, 100, 750])
def test_wpm_chart_keeps_fixed_ten_point_scale(peak):
    chart = wpm_chart([(0, 0), (10, peak)], width=11)
    rows = chart.splitlines()[2:11]
    assert [int(row.split("|")[0]) for row in rows] == [100, 90, 80, 70, 60, 50, 40, 30, 20]
    assert rows[-1][5] == "*"
    if peak >= 100:
        assert rows[0][-1] == "*"
    else:
        assert rows[7][-1] == "*"
    assert all(len(row) == 16 for row in rows)
