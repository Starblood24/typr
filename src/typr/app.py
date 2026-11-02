from dataclasses import fields, replace
import json
from pathlib import Path
import sqlite3

from textual.app import App
from textual.binding import Binding

from .core.typing_engine import Session, SessionStatus
from .modes.classic import ClassicConfig, generate
from .modes.story import load_stories
from .storage.database import Database, DEFAULTS
from .ui.screens import (BootScreen, HomeScreen, TypingScreen, PauseScreen, ResultsScreen,
                         StoryDirectoryScreen, ChapterIntroScreen, StoryCompleteScreen,
                         ConfirmScreen, ErrorScreen, SettingsScreen, DataScreen, StatsScreen)
from .ui.widgets import TypingView


class TyprApp(App):
    CSS_PATH = "ui/base.tcss"
    BINDINGS = [Binding("ctrl+c", "request_quit", show=False, priority=True),
                Binding("ctrl+r", "restart_current", show=False, priority=True)]
    ENABLE_COMMAND_PALETTE = False

    def terminal_cursor(self):
        view = self.focused
        if (isinstance(self.screen, TypingScreen) and isinstance(view, TypingView)
                and not self.screen.has_class("tiny") and view.visible):
            position = view.content_region.offset + view.caret_offset
            body = self.screen.query_one(".body")
            if body.content_region.contains(position.x, position.y):
                visible = view.blink or self.settings["cursor blink"] == "off"
                return f"\x1b[{position.y + 1};{position.x + 1}H\x1b[6 q\x1b[?25{'h' if visible else 'l'}"
        return "\x1b[0 q\x1b[?25l"

    # shortcut: Textual 8.2.8 has no visible-caret API; revisit these hooks when upgrading.
    def _begin_update(self):
        super()._begin_update()
        if not self.is_headless and self._driver:
            self._driver.write("\x1b[?25l")

    def _end_update(self):
        if not self.is_headless and self._driver:
            self._driver.write(self.terminal_cursor())
        super()._end_update()

    def __init__(self, data_dir: Path, skip_boot=False):
        super().__init__()
        self.data_dir, self.skip_boot = Path(data_dir), skip_boot
        self.settings = DEFAULTS.copy()
        self.classic_config = ClassicConfig()
        self.db = None
        self.session = None
        self.story = None
        self.paragraph = 0
        self.original_text = ""
        self.saving = False

    def on_mount(self):
        self.set_interval(.1, self.tick)
        self.io(self.initialize, self.show_start)

    def initialize(self):
        if self.db is None:
            self.db = Database(self.data_dir / "typr.db")
        settings = self.db.settings()
        self.settings = {k: settings.get(k) if settings.get(k) in ("on", "off", "subtle") else v for k, v in DEFAULTS.items()}
        try:
            data = json.loads(settings.get("classic", "{}"))
            self.classic_config = ClassicConfig(**{f.name: data[f.name] for f in fields(ClassicConfig) if f.name in data})
            self.classic_config.validate()
        except (ValueError, TypeError, KeyError):
            self.classic_config = ClassicConfig()

    def show_start(self, _):
        self.push_screen(HomeScreen() if self.skip_boot else BootScreen())

    def io(self, operation, success=lambda _: None):
        try:
            result = operation()
        except (OSError, sqlite3.Error, ValueError, TypeError, KeyError) as error:
            back, label = None, "back"
            if len(self.screen_stack) == 1:
                back, label = self.goodbye, "quit"
            elif self.saving and self.session is not None:
                back = lambda: self.push_screen(ConfirmScreen(
                    "discard this unsaved session?", self.abort))
                label = "discard session"
            self.push_screen(ErrorScreen(str(error), lambda: self.io(operation, success), back, label))
            return
        success(result)

    def return_home(self):
        self.session = None
        self.story = None
        self.saving = False
        while len(self.screen_stack) > 2:
            self.pop_screen()
        if not isinstance(self.screen, HomeScreen):
            self.switch_screen(HomeScreen())

    def save_config_and_start(self):
        self.io(lambda: self.db.setting("classic", json.dumps(self.classic_config.as_dict())), lambda _: self.start_classic())

    def start_classic(self, text=None, config=None):
        self.story = None
        self.session_config = replace(config if config is not None else self.classic_config)
        self.original_text = text if text is not None else generate(self.session_config)
        self.session = Session(self.original_text, self.session_config.length if self.session_config.test_type == "time" else None)
        self.saving = False
        self.replace_session_screen(TypingScreen())

    def replace_session_screen(self, screen):
        while len(self.screen_stack) > 2 and isinstance(self.screen, (PauseScreen, SettingsScreen, DataScreen, ConfirmScreen, ErrorScreen)):
            self.pop_screen()
        if isinstance(self.screen, (TypingScreen, ResultsScreen, ChapterIntroScreen, StoryCompleteScreen)):
            self.switch_screen(screen)
        else:
            self.push_screen(screen)

    def tick(self):
        session = self.session
        if not session or self.saving:
            return
        session.tick()
        if session.status is SessionStatus.FINISHED and not self.story and not isinstance(self.screen, ResultsScreen):
            self.complete_classic()
            return
        if not self.screen.is_mounted:
            return
        if isinstance(self.screen, (TypingScreen, PauseScreen)) and self.screen.query("#metrics, #remaining"):
            self.screen.refresh_session()
        if isinstance(self.screen, TypingScreen) and self.screen.query(TypingView):
            view = self.screen.query_one(TypingView)
            active = session.last_input is not None and session.clock() - session.last_input < .8
            view.blink = active or int(session.clock() / .6) % 2 == 0

    def after_input(self):
        if self.saving:
            return
        s = self.session
        if s.status is SessionStatus.FINISHED:
            if not self.story:
                self.complete_classic()
            return
        if s.complete:
            if self.story:
                next_index = self.paragraph + 1
                self.saving = True
                self.io(lambda: self.db.checkpoint(self.story.id, next_index), lambda _: self.advance_story(next_index))
            elif s.duration:
                s.target += " " + generate(self.session_config)
                self.original_text = s.target
            else:
                s.finish()
                self.complete_classic()
        if isinstance(self.screen, TypingScreen):
            self.screen.refresh_session()

    def complete_classic(self):
        if self.saving:
            return
        self.saving = True
        self.io(lambda: self.db.save_session(self.session_config, self.session), lambda _: self.replace_session_screen(ResultsScreen()))

    def restart(self):
        self.saving = False
        if self.story:
            # Completed paragraphs are immutable; restart only the current paragraph.
            self.session = Session(self.story.paragraphs[self.paragraph][2], None, strict=True)
            self.replace_session_screen(TypingScreen())
        else:
            self.start_classic(self.original_text, self.session_config)

    def action_restart_current(self):
        if self.saving and isinstance(self.screen, (ErrorScreen, ConfirmScreen)):
            return
        if self.story and self.paragraph >= len(self.story.paragraphs):
            return
        if self.session and isinstance(self.screen, (TypingScreen, PauseScreen, ResultsScreen, ConfirmScreen, ErrorScreen)):
            self.restart()

    def abort(self):
        self.session.status = SessionStatus.ABORTED
        self.return_home()

    def open_stories(self):
        self.io(load_stories, lambda stories: self.push_screen(StoryDirectoryScreen(stories)))

    def start_story(self, story, paragraph):
        self.story = story
        self.paragraph = min(paragraph, len(story.paragraphs))
        self.session = None
        self.saving = False
        if self.paragraph == len(story.paragraphs):
            self.replace_session_screen(StoryCompleteScreen())
        else:
            chapter, paragraph_in_chapter, _ = story.paragraphs[self.paragraph]
            if paragraph_in_chapter == 0 and story.chapters[chapter].get("art"):
                self.replace_session_screen(ChapterIntroScreen(story, self.paragraph))
            else:
                self.begin_story_paragraph()

    def begin_story_paragraph(self):
        if self.session is None:
            self.session = Session(self.story.paragraphs[self.paragraph][2], None, strict=True)
        self.saving = False
        self.replace_session_screen(TypingScreen())

    def advance_story(self, next_index):
        old_chapter = self.story.paragraphs[self.paragraph][0]
        self.paragraph = next_index
        self.saving = False
        if next_index == len(self.story.paragraphs):
            self.session.finish()
            self.replace_session_screen(StoryCompleteScreen())
            return
        chapter, _, target = self.story.paragraphs[next_index]
        self.session.next_paragraph(target)
        if chapter != old_chapter and self.story.chapters[chapter].get("art"):
            self.replace_session_screen(ChapterIntroScreen(self.story, next_index))

    def open_stats(self):
        self.io(self.db.stats, lambda data: self.push_screen(StatsScreen(data)))

    def restart_story(self, story):
        self.io(lambda: self.db.restart_story(story.id), lambda _: self.start_story(story, 0))

    def reset_data(self):
        def done(_):
            self.settings = DEFAULTS.copy()
            self.classic_config = ClassicConfig()
            self.return_home()
            self.push_screen(SettingsScreen())
        self.io(self.db.reset, done)

    def action_request_quit(self):
        if isinstance(self.screen, HomeScreen):
            self.screen.request_quit()
        elif not isinstance(self.screen, ConfirmScreen):
            self.push_screen(ConfirmScreen("terminate typr? incomplete Classic progress will be discarded.", self.goodbye))

    def goodbye(self):
        self.exit(message="typr_ / channel closed. goodbye.")

    def on_unmount(self):
        if not self.is_headless and self._driver:
            self._driver.write("\x1b[0 q")
            self._driver.flush()
        if self.db:
            self.db.close()
