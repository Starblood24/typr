import ast
import json
import random
from importlib.resources import files

import pytest

from typr.modes.classic import ClassicConfig, generate
from typr.core.typing_engine import Session, SessionStatus
from typr.app import TyprApp
from typr.ui.screens import ClassicSetupScreen, TypingScreen, ResultsScreen, PauseScreen
from typr.ui.widgets import TerminalMenu, TypingView


@pytest.mark.parametrize("language", ["python", "javascript", "typescript", "rust"])
def test_complete_snippets_and_new_material(language):
    config = ClassicConfig(mode="developer", code_language=language, test_type="snippet", length=1)
    first = generate(config, random.Random(1))
    assert "\n" in first and "    " in first
    assert "\t" not in first and "\r" not in first
    assert generate(config, previous=first) != first
    bank = json.loads(files("typr").joinpath("assets/code/snippets.json").read_text(encoding="utf-8"))
    assert len(set(bank[language])) == 3
    if language == "python":
        for snippet in bank[language]:
            ast.parse(snippet)


@pytest.mark.parametrize("changes", [dict(code_language="../../private"), dict(test_type="words", length=10),
                                     dict(test_type="snippet", length=10), dict(mode="other")])
def test_invalid_developer_configuration(changes):
    values = dict(mode="developer", test_type="snippet", length=1)
    values.update(changes)
    with pytest.raises(ValueError):
        generate(ClassicConfig(**values))


def test_old_classic_config_remains_valid():
    config = ClassicConfig(**json.loads('{"language":"de","difficulty":"mixed","test_type":"words","length":10}'))
    config.validate()
    assert config.mode == "standard"
    assert len(generate(config).split()) == 10


def test_autoindent_backspace_and_manual_metrics():
    now = [0.0]
    session = Session("if ok:\n    run()\nend()", None, code=True, clock=lambda: now[0])
    for ch in "if ok:\n":
        session.type(ch)
    assert session.typed == "if ok:\n    "
    assert session.automatic == {7, 8, 9, 10}
    assert session.correct == session.attempts == session.correct_attempts == 7
    now[0] = 60
    assert session.wpm == pytest.approx(7 / 5)
    session.backspace()
    assert session.typed == "if ok:\n   "
    session.type(" ")
    assert session.correct == 8 and session.attempts == 8
    for _ in range(6):
        session.backspace()
    assert session.typed == "if ok"
    assert session.automatic == set()


def test_newlines_are_code_only_and_wrong_newline_does_not_autoindent():
    standard = Session("abc", None)
    standard.type("\n")
    assert standard.started is None and not standard.typed
    code = Session("a\n    b", None, code=True)
    code.type("\n")
    assert code.typed == "\n" and code.accuracy == 0
    assert code.automatic == set()


def test_nested_indent_blank_lines_dedent_and_timed_pause():
    now = [0.0]
    text = "fn() {\n    if ok {\n        run();\n    }\n\n}"
    session = Session(text, 15, code=True, clock=lambda: now[0])
    while not session.complete:
        session.type(text[len(session.typed)])
    assert session.typed == text
    assert session.attempts == len(text) - len(session.automatic)
    assert session.accuracy == 100
    session.pause_menu()
    now[0] = 16
    session.tick()
    assert session.status is SessionStatus.FINISHED and session.elapsed == 15


@pytest.mark.parametrize("language,steps", [("python", 0), ("javascript", 1), ("typescript", 2), ("rust", 3)])
async def test_developer_setup_complete_retry_new_and_persistence(tmp_path, language, steps):
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test(size=(100, 36)) as pilot:
        await pilot.press("down", "enter", "right", "down")
        assert isinstance(app.screen, ClassicSetupScreen)
        for _ in range(steps):
            await pilot.press("right")
        assert app.screen.config.code_language == language
        assert app.screen.config.test_type == "snippet"
        assert "difficulty" not in [key for _, key in app.screen.options()]
        await pilot.press("down", "down", "enter")
        assert isinstance(app.screen, TypingScreen)
        assert app.session.code and app.session.duration is None
        text = app.session.target
        while not isinstance(app.screen, ResultsScreen):
            app.session.type(text[len(app.session.typed)])
            app.after_input()
        assert app.session.typed == text
        assert app.session.correct == len(text) - len(app.session.automatic)
        assert app.db.stats()[1][0]["language"] == language
        assert json.loads(app.db.stats()[1][0]["config"])["mode"] == "developer"
        await pilot.pause()
        await pilot.press("enter")
        assert app.session.target == text and not app.session.typed and not app.session.automatic
        app.session.finish()
        app.complete_classic()
        await pilot.pause()
        await pilot.press("down", "enter")
        assert app.session.target != text
        assert app.session_config.code_language == language
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test() as pilot:
        assert app.classic_config.mode == "developer" and app.classic_config.code_language == language
        await pilot.press("enter")
        assert not app.session.code and app.session.duration == 30
        assert app.session_config == ClassicConfig()


async def test_code_enter_indent_backspace_and_stable_view(tmp_path):
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test(size=(100, 36)) as pilot:
        config = ClassicConfig(mode="developer", test_type="snippet", length=1)
        target = "if ok:\n    run()\n\nend()"
        app.start_classic(target, config)
        await pilot.pause()
        view = app.screen.query_one(TypingView)
        assert view.render().plain == target
        await pilot.press("i", "f", "space", "o", "k", ":", "enter")
        assert app.session.typed == "if ok:\n    "
        assert app.session.attempts == 7
        assert view.render().plain == target
        assert (view.caret_offset.x, view.caret_offset.y) == (4, 1)
        await pilot.press("backspace")
        assert app.session.typed == "if ok:\n   "
        assert view.render().plain == target
        await pilot.press("escape")
        assert isinstance(app.screen, PauseScreen)
        await pilot.press("ctrl+r")
        assert app.session.code and app.session.target == target
        assert not app.session.automatic and not app.session.typed


async def test_timed_code_extends_with_complete_snippet_and_expires_while_paused(tmp_path):
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test() as pilot:
        config = ClassicConfig(mode="developer", code_language="rust", length=15)
        app.start_classic("fn main() {}", config)
        await pilot.pause()
        for char in "fn main() {}":
            app.session.type(char)
            app.after_input()
        assert app.session.target.startswith("fn main() {}\n\n")
        assert "fn main()" in app.session.target[14:]
        assert app.original_text == app.session.target
        await pilot.press("escape")
        app.session.started -= 16
        app.tick()
        await pilot.pause()
        assert isinstance(app.screen, ResultsScreen)
        assert app.db.stats()[0]["total"] == 1
        await pilot.press("enter")
        assert app.session.code and app.session.duration == 15


@pytest.mark.parametrize("size", [(100, 36), (40, 12)])
async def test_long_code_lines_scroll_without_losing_indentation_or_cursor(tmp_path, size):
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test(size=size) as pilot:
        target = "start()\n    " + "value" * 30 + ";\n\nend()"
        app.start_classic(target, ClassicConfig(mode="developer", test_type="snippet", length=1))
        await pilot.pause()
        view = app.screen.query_one(TypingView)
        for _ in range(len(target) - 2):
            if len(app.session.typed) >= len(target) - 2:
                break
            app.session.type(target[len(app.session.typed)])
            view.render()
            assert 0 <= view.caret_offset.x < view.size.width
            assert 0 <= view.caret_offset.y < view.size.height
        await pilot.resize_terminal(60, 18)
        await pilot.pause()
        view.render()
        assert 0 <= view.caret_offset.x < view.size.width
        assert 0 <= view.caret_offset.y < view.size.height
