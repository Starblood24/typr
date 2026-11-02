import sqlite3

import pytest
from textual.widgets import Static
from unittest.mock import Mock, PropertyMock, patch
from textual.app import App

from typr.app import TyprApp
from typr.core.typing_engine import Session, SessionStatus
from typr.modes.classic import ClassicConfig
from typr.modes.story import load_stories
from typr.storage.database import Database
from typr.ui.screens import (HomeScreen, BootScreen, ClassicSetupScreen, TypingScreen,
                            PauseScreen, ResultsScreen, StoryDirectoryScreen,
                            ChapterIntroScreen, StoryCompleteScreen, SettingsScreen,
                            ConfirmScreen, ErrorScreen, StatsScreen)
from typr.ui.widgets import TerminalMenu, TypingView


async def test_boot_exact_asset_skip_and_menu_selection(tmp_path):
    app = TyprApp(tmp_path)
    async with app.run_test(size=(100, 36)) as pilot:
        assert isinstance(app.screen, BootScreen)
        assert not app.screen.has_class("compact")
        await pilot.press("space")
        assert isinstance(app.screen, HomeScreen)
        await pilot.press("down", "enter")
        assert isinstance(app.screen, ClassicSetupScreen)
        await pilot.press("escape")
        assert app.screen.query_one(TerminalMenu).index == 1
        await pilot.press("q", "enter")
        assert not app.screen.quitting
        await pilot.press("q", "n")
        assert not app.screen.quitting


async def test_setup_options_quick_start_persistence(tmp_path):
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test(size=(100, 36)) as pilot:
        await pilot.press("down", "enter", "down", "right")
        assert app.screen.config.language == "de"
        await pilot.press("down", "right", "down", "right")
        assert app.screen.config.test_type == "words"
        assert app.screen.config.length == 25
        await pilot.press("down", "right", "down", "enter")
        assert isinstance(app.screen, TypingScreen)
        assert app.classic_config.length == 50
        await pilot.press("escape", "down", "down", "enter")
        assert isinstance(app.screen, ConfirmScreen)
        await pilot.press("y")
        assert isinstance(app.screen, HomeScreen)
        assert app.db.stats()[0]["total"] == 0
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test() as pilot:
        await pilot.press("enter")
        assert isinstance(app.screen, TypingScreen)
        assert app.classic_config.language == "de"
        assert len(app.session.target.split()) == 50


async def test_typing_results_retry_new_and_stats(tmp_path):
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test(size=(100, 36)) as pilot:
        app.classic_config = ClassicConfig(test_type="words", length=10)
        app.start_classic("für dich")
        await pilot.pause()
        for ch in "für dich":
            await pilot.press(ch if ch != " " else "space")
        assert isinstance(app.screen, ResultsScreen)
        assert app.db.stats()[0]["total"] == 1
        await pilot.press("enter")
        assert app.session.target == "für dich"
        assert app.session.typed == ""
        await pilot.press("ctrl+r")
        assert app.session.target == "für dich"
        app.session.finish()
        app.complete_classic()
        await pilot.pause()
        await pilot.press("down", "enter")
        assert app.session.target != "für dich"
        assert app.classic_config.length == 10
        app.return_home()
        app.open_stats()
        await pilot.pause()
        assert isinstance(app.screen, StatsScreen)


async def test_pause_expiration_and_single_save(tmp_path):
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test() as pilot:
        await pilot.press("enter", "a", "escape")
        assert isinstance(app.screen, PauseScreen)
        app.session.started -= 31
        app.tick()
        await pilot.pause()
        assert isinstance(app.screen, ResultsScreen)
        app.tick()
        app.complete_classic()
        assert app.db.stats()[0]["total"] == 1


async def test_story_strict_autosave_resume_and_filter(tmp_path):
    app = TyprApp(tmp_path, skip_boot=True)
    story = next(s for s in load_stories() if s.language == "de")
    async with app.run_test(size=(100, 36)) as pilot:
        await pilot.press("down", "down", "enter", "right")
        assert isinstance(app.screen, StoryDirectoryScreen)
        assert app.screen.language == "de"
        await pilot.press("enter", "enter")
        assert isinstance(app.screen, TypingScreen)
        first = app.session.target
        await pilot.press("x", first[0])
        assert app.session.typed == "x"
        await pilot.press("backspace")
        for ch in first:
            app.session.type(ch)
            app.after_input()
        await pilot.pause()
        assert app.paragraph == 1
        assert app.session.typed == ""
        assert app.db.progress(story.id) == 1
        assert isinstance(app.screen, TypingScreen)
        await pilot.press("backspace")
        assert app.session.typed == ""
        app.session.type(app.session.target[0])
        assert app.db.stats()[0]["total"] == 0
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test() as pilot:
        app.start_story(story, app.db.progress(story.id))
        await pilot.pause()
        assert isinstance(app.screen, TypingScreen)
        assert app.session.target == story.paragraphs[1][2]
        assert app.session.typed == ""


async def test_story_complete_chapter_transitions_restart_confirmation(tmp_path):
    app = TyprApp(tmp_path, skip_boot=True)
    story = load_stories()[0]
    async with app.run_test(size=(100, 36)) as pilot:
        app.open_stories()
        await pilot.pause()
        app.start_story(story, 0)
        await pilot.pause()
        await pilot.press("enter")
        for paragraph in story.paragraphs:
            if isinstance(app.screen, ChapterIntroScreen):
                await pilot.press("enter")
            for ch in paragraph[2]:
                app.session.type(ch)
                app.after_input()
            await pilot.pause()
        assert isinstance(app.screen, StoryCompleteScreen)
        assert app.db.progress(story.id) == len(story.paragraphs)
        await pilot.press("enter")
        menu = app.screen.query_one(TerminalMenu)
        for _ in range(len(app.screen.visible)):
            await pilot.press("down")
        assert menu.selected == "restart"
        await pilot.press("enter")
        assert isinstance(app.screen, ConfirmScreen)
        await pilot.press("n")
        assert app.db.progress(story.id) == len(story.paragraphs)
        await pilot.press("enter", "y")
        assert isinstance(app.screen, ChapterIntroScreen)
        restarted = app.story
        assert app.db.progress(restarted.id) == 0


@pytest.mark.parametrize("size", [(120,40),(80,24),(60,18),(40,12),(32,10)])
async def test_resize_keyboard_compact_cursor_visible(tmp_path, size):
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test(size=size) as pilot:
        assert app.screen.has_class("tiny") == (size[0] < 40 or size[1] < 12)
        await pilot.resize_terminal(100,36)
        app.start_classic("für dich " * 40)
        await pilot.pause()
        for ch in "für dich " * 10:
            app.session.type(ch)
        view = app.screen.query_one(TypingView)
        view.refresh()
        await pilot.resize_terminal(40,12)
        await pilot.pause()
        app.settings["cursor blink"] = "off"
        assert "\x1b[6 q" in app.terminal_cursor()
        assert len(view.render().plain.splitlines()) <= 1
        await pilot.resize_terminal(120,40)
        await pilot.pause()
        assert not app.screen.has_class("compact")


async def test_settings_autosave_ascii_and_data_reset(tmp_path):
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test(size=(100,36)) as pilot:
        for _ in range(4):
            await pilot.press("down")
        await pilot.press("enter", "down", "down", "right")
        assert isinstance(app.screen, SettingsScreen)
        assert app.settings["ascii art"] == "off"
        assert app.db.settings()["ascii art"] == "off"
        assert app.screen.has_class("compact")
        await pilot.press("down", "enter", "enter")
        assert isinstance(app.screen, ConfirmScreen)
        await pilot.press("enter")
        assert app.db.settings()["ascii art"] == "off"
        await pilot.press("enter", "y")
        assert isinstance(app.screen, SettingsScreen)
        assert app.settings["ascii art"] == "on"


async def test_storage_error_retry_and_quit_request(tmp_path):
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test() as pilot:
        state = {"fail": True, "success": False}
        def operation():
            if state["fail"]:
                raise sqlite3.OperationalError("test database unavailable")
        app.io(operation, lambda _: state.update(success=True))
        await pilot.pause()
        assert isinstance(app.screen, ErrorScreen)
        state["fail"] = False
        await pilot.press("enter")
        assert state["success"]
        assert isinstance(app.screen, HomeScreen)
        await pilot.press("ctrl+c")
        assert app.screen.quitting


async def test_boot_automatically_finishes_without_animation_delays(tmp_path):
    db = Database(tmp_path / "typr.db")
    db.setting("animations", "off")
    db.close()
    app = TyprApp(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause(.2)
        assert isinstance(app.screen, HomeScreen)


async def test_global_restart_from_pause_and_paste_rejection(tmp_path):
    from textual.events import Paste
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test() as pilot:
        await pilot.press("enter", "a", "escape", "ctrl+r")
        assert isinstance(app.screen, TypingScreen)
        assert app.session.typed == ""
        assert app.session.started is None
        app.screen.query_one(TypingView).post_message(Paste("pasted text"))
        await pilot.pause()
        assert app.session.typed == ""


async def test_render_colors_active_cursor_and_versions(tmp_path):
    from typr.ui.widgets import PALETTE
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test(size=(100,36)) as pilot:
        app.start_classic("für dich " * 10)
        await pilot.pause()
        await pilot.press("f", "x")
        app.tick()
        rendered = app.screen.query_one(TypingView).render()
        styles = [span.style for span in rendered.spans]
        assert PALETTE["correct"] in styles
        assert PALETTE["pending"] in styles
        assert any(PALETTE["error_background"] in str(style) for style in styles)
        assert app.terminal_cursor().endswith("\x1b[?25h")
        assert "v0.1.0" not in str(app.screen.query_one(".header", Static).render())
        await pilot.press("escape")
        assert "v0.1.0" in str(app.screen.query_one(".header", Static).render())


async def test_cursor_never_changes_target_characters_or_positions(tmp_path):
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test(size=(100, 36)) as pilot:
        target = "für schöne Wörter bleibt der Text unverändert"
        app.start_classic(target)
        await pilot.pause()
        view = app.screen.query_one(TypingView)
        for ch in "für schöne":
            app.session.type(ch)
            for visible in (True, False):
                view.blink = visible
                assert view.render().plain == target
            view.blink = True
            assert view.caret_offset.x == len(app.session.typed)
            assert view.caret_offset.y == 0
        for _ in range(5):
            app.session.backspace()
            assert view.render().plain == target


async def test_art_survives_short_wide_terminal_and_respects_setting(tmp_path):
    app = TyprApp(tmp_path)
    async with app.run_test(size=(120, 24)) as pilot:
        boot = app.screen
        boot.timer.stop()
        assert boot.query_one(".art", Static).display
        await pilot.resize_terminal(120, 40)
        await pilot.pause()
        assert boot.query_one(".art", Static).display
        await pilot.resize_terminal(40, 24)
        await pilot.pause()
        assert not boot.query_one(".art", Static).display
        await pilot.resize_terminal(120, 24)
        await pilot.press("space")
        assert isinstance(app.screen, HomeScreen)
        assert app.screen.query_one(".art", Static).display
        app.settings["ascii art"] = "off"
        app.screen.responsive()
        await pilot.pause()
        assert not app.screen.query_one(".art", Static).display


async def test_boot_status_lines_remain_readable_before_finishing(tmp_path):
    app = TyprApp(tmp_path)
    async with app.run_test(size=(100, 36)) as pilot:
        await pilot.pause(1.65)
        assert isinstance(app.screen, BootScreen)
        assert 1 <= app.screen.step <= 3
        assert "memory" in str(app.screen.query_one("#boot-log", Static).render())
        await pilot.press("space")
        assert isinstance(app.screen, HomeScreen)


async def test_native_bar_preserves_pending_color_and_hides_outside_typing(tmp_path):
    from typr.ui.widgets import PALETTE
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test(size=(80, 24)) as pilot:
        assert app.terminal_cursor().endswith("\x1b[?25l")
        app.start_classic("für dich " * 20)
        await pilot.pause()
        view = app.screen.query_one(TypingView)
        await pilot.press("f")
        rendered = view.render()
        cursor = len(app.session.typed)
        assert all(s.style == PALETTE["pending"] for s in rendered.spans if s.start <= cursor < s.end)
        assert rendered.plain.startswith("für dich")
        view.blink = True
        assert "\x1b[6 q" in app.terminal_cursor()
        assert app.terminal_cursor().endswith("\x1b[?25h")
        view.blink = False
        assert app.terminal_cursor().endswith("\x1b[?25l")
        app.settings["cursor blink"] = "off"
        assert app.terminal_cursor().endswith("\x1b[?25h")
        for character in "ür dich " * 12:
            app.session.type(character)
        await pilot.resize_terminal(40, 12)
        await pilot.pause()
        view.render()
        assert view.caret_offset.x < view.size.width
        assert app.terminal_cursor().endswith("\x1b[?25h")
        await pilot.press("escape")
        assert app.terminal_cursor() == "\x1b[0 q\x1b[?25l"


@pytest.mark.parametrize("mode", ["classic", "story"])
@pytest.mark.parametrize("recover", ["retry", "discard"])
async def test_failed_save_retries_or_confirms_discard(tmp_path, mode, recover):
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test() as pilot:
        if mode == "classic":
            app.classic_config = ClassicConfig(test_type="words", length=10)
            app.start_classic("a")
            operation = "save_session"
        else:
            story = load_stories()[0]
            app.open_stories()
            await pilot.pause()
            app.start_story(story, 0)
            await pilot.pause()
            await pilot.press("enter")
            operation = "checkpoint"
        await pilot.pause()
        original = getattr(app.db, operation)
        failing = True
        def save(*args):
            if failing:
                raise sqlite3.OperationalError("database is locked")
            return original(*args)
        with patch.object(app.db, operation, side_effect=save):
            for ch in app.session.target:
                app.session.type(ch)
                app.after_input()
            await pilot.pause()
            assert isinstance(app.screen, ErrorScreen)
            assert app.screen.back_label == "discard session"
            assert app.saving
            await pilot.press("escape")
            assert isinstance(app.screen, ConfirmScreen)
            await pilot.press("n", "ctrl+r")
            assert isinstance(app.screen, ErrorScreen)
            if recover == "retry":
                failing = False
                await pilot.press("enter")
                if mode == "classic":
                    assert isinstance(app.screen, ResultsScreen)
                    assert app.db.stats()[0]["total"] == 1
                else:
                    assert isinstance(app.screen, TypingScreen)
                    assert app.db.progress(story.id) == 1
                    assert app.session.typed == ""
                    assert not app.saving
            else:
                await pilot.press("down", "enter")
                assert isinstance(app.screen, ConfirmScreen)
                await pilot.press("y")
                assert isinstance(app.screen, HomeScreen)
                assert app.session is None and not app.saving
                assert app.db.stats()[0]["total"] == 0
                if mode == "story":
                    assert app.db.progress(story.id) == 0


@pytest.mark.parametrize("choice", ["retry", "quit", "escape"])
async def test_startup_failure_has_retry_and_quit(tmp_path, choice):
    bad_path = tmp_path / "profile"
    bad_path.write_text("not a directory")
    app = TyprApp(bad_path, skip_boot=True)
    async with app.run_test() as pilot:
        assert isinstance(app.screen, ErrorScreen)
        assert app.screen.back_label == "quit"
        if choice == "retry":
            bad_path.unlink()
            await pilot.press("enter")
            assert isinstance(app.screen, HomeScreen)
        elif choice == "quit":
            await pilot.press("down", "enter")
            assert app._exit
        else:
            await pilot.press("escape")
            assert app._exit


async def test_tab_keeps_typing_focus_and_input(tmp_path):
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test() as pilot:
        app.start_classic("abc " * 20)
        await pilot.pause()
        await pilot.press("a", "tab", "b", "shift+tab", "c")
        assert isinstance(app.focused, TypingView)
        assert app.session.typed == "abc"
        await pilot.press("escape", "escape", "tab", "space")
        assert isinstance(app.focused, TypingView)
        assert app.session.typed == "abc "


async def test_common_mount_setup_runs_once(tmp_path):
    from typr.ui.screens import UtilityScreen
    original = UtilityScreen.on_mount
    calls = []
    def counted(screen):
        calls.append(type(screen))
        original(screen)
    with patch.object(UtilityScreen, "on_mount", counted):
        app = TyprApp(tmp_path, skip_boot=True)
        async with app.run_test() as pilot:
            await pilot.press("down", "enter", "escape", "up", "enter", "escape")
            assert calls.count(HomeScreen) == 1
            assert calls.count(ClassicSetupScreen) == 1
            assert calls.count(TypingScreen) == 1
            assert calls.count(PauseScreen) == 1


async def test_cursor_commands_reach_driver_and_restore_on_exit(tmp_path):
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test() as pilot:
        await pilot.press("enter", "a")
        view = app.screen.query_one(TypingView)
        view.render()
        view.blink = True
        driver = Mock()
        def check_frame():
            expected = app.terminal_cursor()
            driver.reset_mock()
            with patch.object(App, "is_headless", new_callable=PropertyMock, return_value=False), \
                 patch.object(App, "_display"), patch.object(app, "_driver", driver):
                app._display(app.screen, object())
            driver.write.assert_called_once_with(expected)
            driver.flush.assert_called_once_with()
        check_frame()
        view.blink = False
        check_frame()
        await pilot.press("escape")
        check_frame()
        driver.reset_mock()
        with patch.object(App, "is_headless", new_callable=PropertyMock, return_value=False), \
             patch.object(app, "_driver", driver), patch.object(app, "db", Mock()):
            app.on_unmount()
        driver.write.assert_called_once_with("\x1b[0 q")
        driver.flush.assert_called_once_with()
