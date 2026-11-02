from dataclasses import replace
from textual import events
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Static

from typr.core.typing_engine import SessionStatus
from typr.modes.classic import ClassicConfig
from .widgets import TerminalMenu, TypingView, art, clock_text, progress, wpm_chart


class UtilityScreen(Screen):
    title_text = "home"
    footer_text = "↑↓ navigate   enter select   esc back"

    def compose(self):
        header = "typr_" if self.title_text == "home" else f"typr_ / {self.title_text}"
        if self.title_text in ("home", "paused"):
            header += "    v0.1.0"
        yield Static(header, classes="header", markup=False)
        with VerticalScroll(classes="body"):
            yield from self.body()
        yield Static("terminal too small.\nminimum: 40 × 12\nresize to continue_", id="resize-notice")
        yield Static(self.footer_text, classes="footer", markup=False)

    def body(self):
        return []

    def on_mount(self):
        self.responsive()
        if self.app.settings["animations"] == "subtle" and self.title_text not in ("classic / typing", "results"):
            self.styles.opacity = .8
            self.styles.animate("opacity", 1, duration=.08)

    def on_screen_resume(self):
        self.responsive()

    def on_resize(self, event):
        self.responsive(event.size)

    def responsive(self, size=None):
        size = size or self.app.size
        self.set_class(size.width < 40 or size.height < 12, "tiny")
        self.set_class(size.width < 76 or size.height < 30
                       or self.app.settings.get("ascii art") == "off", "compact")
        from rich.cells import cell_len
        artwork_width = max((max(map(cell_len, str(widget.content).splitlines()), default=0)
                             for widget in self.query(".art")), default=0)
        # Short windows scroll tall artwork; only insufficient width hides it.
        self.set_class(self.app.settings.get("ascii art") == "off"
                       or size.width < artwork_width + 6 + 32 + 4, "hide-art")
        if self.is_mounted:
            for info in self.query("#boot-info"):
                info.styles.height = min(24, max(8, size.height - (4 if self.has_class("compact") else 5)))
            for view in self.query(TypingView):
                view.styles.height = 1 if size.height < 15 else 2 if size.height < 18 else 3
            footer = self.query_one(".footer", Static)
            footer.update(self.footer_text.replace("navigate", "move").replace("select", "go").replace("continue", "go") if size.width < 60 else self.footer_text)

    def on_key(self, event):
        event.prevent_default()
        if event.key == "escape":
            self.app.pop_screen()
            event.stop()


class BootScreen(UtilityScreen):
    title_text = "starOS"
    footer_text = "any key to skip"

    def body(self):
        with Horizontal(classes="split"):
            star = art("staros_star")
            from rich.cells import cell_len
            image = Static(star, classes="art", markup=False)
            image.styles.width = max(map(cell_len, star.splitlines()))
            yield image
            with Vertical(classes="right", id="boot-info"):
                yield Static("starOS [version 0.1]\nTYPR TERMINAL SUBSYSTEM")
                yield Static("", id="boot-log", markup=False)
                with Vertical(id="boot-status"):
                    yield Static(progress(0), id="boot-progress", markup=False)
                    yield Static("", id="boot-ready", markup=False)

    def on_mount(self):
        self.step = 0
        self.timer = self.set_interval(.75 if self.app.settings["animations"] == "subtle" else .02, self.advance)

    def advance(self):
        lines = ["memory ............. ok", "language banks ..... ok", "story archive ...... ok", "input driver ....... ok"]
        self.step += 1
        self.query_one("#boot-log", Static).update("\n".join(lines[:self.step]))
        self.query_one("#boot-progress", Static).update(progress(self.step / 5))
        self.query_one("#boot-ready", Static).update("system ready_" if self.step >= 5 else "")
        if self.step >= 6:
            self.timer.stop()
            self.app.switch_screen(HomeScreen())

    def on_key(self, event):
        event.prevent_default()
        self.timer.stop()
        self.app.switch_screen(HomeScreen())
        event.stop()


class HomeScreen(UtilityScreen):
    footer_text = "↑↓ navigate   enter select   q/esc quit"

    def body(self):
        with Horizontal(classes="split"):
            yield Static(art("typr_logo"), classes="art", markup=False)
            with Vertical(classes="right"):
                yield TerminalMenu([(s, s) for s in ("quick start", "classic", "story", "stats", "settings", "quit")])
                yield Static("", id="quit-prompt", markup=False)

    def on_mount(self):
        self.quitting = False

    def request_quit(self):
        self.quitting = True
        self.query_one("#quit-prompt", Static).update("terminate? [y/N] _")
        self.query_one(".footer", Static).update("y confirm   n cancel   esc cancel")

    def cancel_quit(self):
        self.quitting = False
        self.query_one("#quit-prompt", Static).update("")
        self.query_one(".footer", Static).update(self.footer_text)

    def on_key(self, event):
        event.prevent_default()
        if self.quitting:
            if event.key == "y":
                self.app.goodbye()
            elif event.key in ("n", "escape", "enter"):
                self.cancel_quit()
            event.stop()
        elif event.key in ("q", "escape"):
            self.request_quit()
            event.stop()

    def on_terminal_menu_selected(self, event):
        if self.quitting:
            self.cancel_quit()
            return
        match event.key:
            case "quick start": self.app.start_classic(config=ClassicConfig())
            case "classic": self.app.push_screen(ClassicSetupScreen())
            case "story": self.app.open_stories()
            case "stats": self.app.open_stats()
            case "settings": self.app.push_screen(SettingsScreen())
            case "quit": self.request_quit()


class ClassicSetupScreen(UtilityScreen):
    title_text = "classic / setup"
    footer_text = "↑↓ navigate   ←→ change   enter select   esc back"

    def __init__(self):
        super().__init__()
        self.config = None

    def options(self):
        c = self.config
        return [("[ CONTENT ]", None), ("mode          < standard >", "mode"),
                (f"language      < {'english' if c.language == 'en' else 'deutsch'} >", "language"),
                (f"difficulty    < {c.difficulty} >", "difficulty"), ("", None),
                ("[ SESSION ]", None), (f"test type     < {c.test_type} >", "test_type"),
                (f"{'duration' if c.test_type == 'time' else 'words':14}< {c.length}{'s' if c.test_type == 'time' else ''} >", "length"),
                ("", None), ("start test", "start")]

    def body(self):
        self.config = replace(self.app.classic_config)
        yield TerminalMenu(self.options())
        yield Static(self.command(), id="command", classes="notice", markup=False)

    def command(self):
        c = self.config
        return f"$ typr --mode standard --lang {c.language} --difficulty {c.difficulty} --{c.test_type} {c.length}"

    def change(self, step):
        key = self.query_one(TerminalMenu).selected
        choices = {"language": ("en", "de"), "difficulty": ("common", "mixed", "advanced"),
                   "test_type": ("time", "words"), "length": (15, 30, 60, 120) if self.config.test_type == "time" else (10, 25, 50, 100)}
        if key not in choices:
            return
        values = choices[key]
        setattr(self.config, key, values[(values.index(getattr(self.config, key)) + step) % len(values)])
        if key == "test_type":
            self.config.length = 30 if self.config.test_type == "time" else 25
        self.query_one(TerminalMenu).relabel(self.options())
        self.query_one("#command", Static).update(self.command())

    def on_key(self, event):
        event.prevent_default()
        if event.key in ("left", "right"):
            self.change(1 if event.key == "right" else -1)
            event.stop()
        else:
            super().on_key(event)

    def on_terminal_menu_selected(self, event):
        if event.key == "start":
            self.app.classic_config = replace(self.config)
            self.app.save_config_and_start()
        else:
            self.change(1)


class TypingScreen(UtilityScreen):
    footer_text = "esc pause"

    def __init__(self):
        super().__init__()
        self.title_text = "classic / typing"

    def body(self):
        yield Static("", id="chapter", classes="notice", markup=False)
        yield Static("", id="metrics", markup=False)
        yield TypingView()
        yield Static("", id="progress", markup=False)

    def on_mount(self):
        self.query_one(VerticalScroll).can_focus = False
        self.query_one(TypingView).focus()
        self.refresh_session()

    def refresh_session(self):
        s = self.app.session
        if not s:
            return
        story = self.app.story
        if story:
            c, p, _ = story.paragraphs[self.app.paragraph]
            self.query_one(".header", Static).update(f"typr_ / story / {story.title}")
            self.query_one("#chapter", Static).update(f"chapter {c+1:02} / {len(story.chapters):02}\nparagraph {p+1:02} / {len(story.chapters[c]['paragraphs']):02}")
            fraction = (self.app.paragraph + len(s.typed)/len(s.target)) / len(story.paragraphs)
        else:
            self.query_one("#chapter", Static).display = False
            fraction = s.elapsed / s.duration if s.duration else len(s.typed) / len(s.target)
        time = s.remaining if s.duration else s.elapsed
        self.query_one("#metrics", Static).update(f"{clock_text(time)}    {s.wpm:.0f} wpm    {s.accuracy:.0f}% acc")
        self.query_one("#progress", Static).update("progress " + progress(fraction))
        self.query_one(TypingView).refresh()

    def on_key(self, event):
        event.prevent_default()
        if event.key == "escape":
            self.app.session.pause_menu()
            self.app.push_screen(PauseScreen())
            event.stop()
        elif event.key == "ctrl+r":
            self.app.restart()
            event.stop()


class PauseScreen(UtilityScreen):
    title_text = "paused"
    footer_text = "↑↓ navigate   enter select   esc resume"

    def body(self):
        yield Static("session paused.", classes="spaced")
        yield Static("", id="remaining", classes="spaced", markup=False)
        yield TerminalMenu([(s, s) for s in ("resume", "restart", "settings", "abort")])

    def on_mount(self):
        self.refresh_session()

    def refresh_session(self):
        s = self.app.session
        self.query_one("#remaining", Static).update(("time remaining    " + clock_text(s.remaining)) if s.duration else "elapsed    " + clock_text(s.elapsed))

    def on_key(self, event):
        event.prevent_default()
        if event.key == "escape":
            self.app.session.resume()
            self.app.pop_screen()
            event.stop()

    def on_terminal_menu_selected(self, event):
        if event.key == "resume":
            self.app.session.resume()
            self.app.pop_screen()
        elif event.key == "restart":
            self.app.restart()
        elif event.key == "settings":
            self.app.push_screen(SettingsScreen())
        else:
            self.app.push_screen(ConfirmScreen("discard this incomplete session?", self.app.abort))


class ResultsScreen(UtilityScreen):
    title_text = "results"
    footer_text = "↑↓ navigate   enter select"

    def body(self):
        s = self.app.session
        yield Static(f"session complete.\n\nwpm        {s.wpm:.0f}\naccuracy   {s.accuracy:.0f}%\nduration   {s.elapsed:.1f}s", classes="spaced", markup=False)
        yield Static(wpm_chart(s.samples, width=max(12, min(40, self.app.size.width-12))), classes="spaced", markup=False)
        yield TerminalMenu([(s, s) for s in ("retry", "new test", "main menu")])

    def on_key(self, event):
        event.prevent_default()

    def on_terminal_menu_selected(self, event):
        if event.key == "retry":
            self.app.start_classic(self.app.original_text, self.app.session_config)
        elif event.key == "new test":
            self.app.start_classic(config=self.app.session_config)
        else:
            self.app.return_home()


class StoryDirectoryScreen(UtilityScreen):
    title_text = "stories"
    footer_text = "↑↓ navigate   ←→ filter   enter continue   esc back"

    def __init__(self, stories, language="all"):
        super().__init__()
        self.stories = stories
        self.language = language
        self.selected_story = None

    @property
    def visible(self):
        return [s for s in self.stories if self.language in ("all", s.language)]

    def body(self):
        yield Static(f"language    < {self.language} >    de    en", classes="spaced", markup=False)
        yield Static(f"available stories: {len(self.visible):02}", markup=False)
        yield TerminalMenu([(f"{s.title}    {s.language.upper()}", s.id) for s in self.visible]
                           + [("", None), ("restart selected story", "restart")])
        yield Static("", id="story-details", classes="spaced", markup=False)

    def on_mount(self):
        self.details()

    def details(self):
        key = self.query_one(TerminalMenu).selected
        story = next((s for s in self.visible if s.id == key), self.selected_story)
        if story:
            self.selected_story = story
            self.app.io(lambda: self.app.db.progress(story.id), lambda p: self.show_details(story, p))

    def show_details(self, story, p):
        p = min(p, len(story.paragraphs))
        chapter = story.paragraphs[min(p, len(story.paragraphs)-1)][0] + 1
        self.query_one("#story-details", Static).update(f"selected    {story.title}\nchapter     {chapter:02} / {len(story.chapters):02}\nprogress    {progress(p/len(story.paragraphs))}" + ("\ncompleted" if p == len(story.paragraphs) else ""))

    def on_terminal_menu_changed(self, event):
        self.details()

    def on_key(self, event):
        event.prevent_default()
        if event.key in ("left", "right"):
            choices = ("all", "de", "en")
            lang = choices[(choices.index(self.language) + (1 if event.key == "right" else -1)) % 3]
            self.app.switch_screen(StoryDirectoryScreen(self.stories, lang))
            event.stop()
        else:
            super().on_key(event)

    def on_terminal_menu_selected(self, event):
        if event.key == "restart":
            if self.selected_story:
                self.app.push_screen(ConfirmScreen("restart this story from chapter 1? saved progress will be reset.", lambda: self.app.restart_story(self.selected_story)))
            return
        story = next(s for s in self.visible if s.id == event.key)
        self.app.io(lambda: self.app.db.progress(story.id), lambda p: self.app.start_story(story, p))


class ChapterIntroScreen(UtilityScreen):
    footer_text = "enter begin   esc back"

    def __init__(self, story, paragraph):
        super().__init__()
        self.story, self.paragraph = story, paragraph
        self.title_text = f"story / {story.title}"

    def body(self):
        c, _, _ = self.story.paragraphs[self.paragraph]
        chapter = self.story.chapters[c]
        yield Static(f"chapter {c+1:02} — {chapter['title']}", classes="spaced", markup=False)
        if chapter.get("art"):
            yield Static(chapter["art"], classes="art", markup=False)
        yield Static(chapter.get("intro", ""), classes="spaced", markup=False)
        yield TerminalMenu([("begin chapter", "begin")])

    def on_terminal_menu_selected(self, event):
        self.app.begin_story_paragraph()


class StoryCompleteScreen(UtilityScreen):
    title_text = "story / complete"

    def body(self):
        yield Static(f"{self.app.story.title}\n\nstory complete.\nprogress {progress(1)}", classes="spaced", markup=False)
        yield TerminalMenu([("story directory", "stories"), ("main menu", "home")])

    def on_terminal_menu_selected(self, event):
        self.app.return_home()
        if event.key == "stories":
            self.app.open_stories()


class StatsScreen(UtilityScreen):
    title_text = "stats"
    footer_text = "↑↓ scroll   esc back"

    def __init__(self, data):
        super().__init__()
        self.data = data

    def body(self):
        s, rows = self.data
        yield Static(f"total sessions     {s['total']}\naverage wpm        {s['average']:.0f}\nbest wpm           {s['best']:.0f}\naverage accuracy   {s['accuracy']:.0f}%\n\nrecent sessions\n", classes="spaced", markup=False)
        yield Static("\n".join(f"  {i:02}   {r['language']}   {r['wpm']:.0f} wpm   {r['accuracy']:.0f}%" for i, r in enumerate(rows, 1)) or "no sessions yet.", markup=False)

    def on_mount(self):
        self.query_one(VerticalScroll).focus()


class SettingsScreen(UtilityScreen):
    title_text = "settings"
    footer_text = "↑↓ navigate   ←→ change   enter select   esc back"

    def options(self):
        return [(f"{k:15} < {self.app.settings[k]} >", k) for k in ("animations", "cursor blink", "ascii art")] + [("data             manage", "data")]

    def body(self):
        yield TerminalMenu(self.options())
        yield Static("changes are saved automatically.", classes="notice", markup=False)
        yield Static("", id="saved", classes="notice", markup=False)

    def change(self):
        key = self.query_one(TerminalMenu).selected
        if key == "data":
            self.app.push_screen(DataScreen())
            return
        value = ("off" if self.app.settings[key] != "off" else ("subtle" if key == "animations" else "on"))
        def saved(_):
            self.app.settings[key] = value
            self.query_one(TerminalMenu).relabel(self.options())
            self.query_one("#saved", Static).update("[ok] configuration saved")
            self.responsive()
        self.app.io(lambda: self.app.db.setting(key, value), saved)

    def on_key(self, event):
        event.prevent_default()
        if event.key in ("left", "right"):
            self.change()
            event.stop()
        else:
            super().on_key(event)

    def on_terminal_menu_selected(self, event):
        self.change()


class DataScreen(UtilityScreen):
    title_text = "settings / data"

    def body(self):
        yield Static(f"local storage\n{self.app.data_dir / 'typr.db'}\n\nreset removes Classic history, Story progress and settings.", classes="spaced", markup=False)
        yield TerminalMenu([("reset saved data", "reset"), ("back", "back")])

    def on_terminal_menu_selected(self, event):
        if event.key == "back":
            self.app.pop_screen()
        else:
            self.app.push_screen(ConfirmScreen("reset all saved data? this cannot be undone.", self.app.reset_data))


class ConfirmScreen(UtilityScreen):
    title_text = "confirm"
    footer_text = "y confirm   n cancel   esc cancel"

    def __init__(self, prompt, confirmed):
        super().__init__()
        self.prompt, self.confirmed = prompt, confirmed

    def body(self):
        yield Static(self.prompt + "\n\n[y/N] _", classes="spaced", markup=False)

    def on_key(self, event):
        event.prevent_default()
        if event.key == "y":
            self.app.pop_screen()
            self.confirmed()
        elif event.key in ("n", "escape", "enter"):
            self.app.pop_screen()
        event.stop()


class ErrorScreen(UtilityScreen):
    title_text = "error"

    def __init__(self, message, retry, back=None, back_label="back"):
        super().__init__()
        self.message, self.retry = message, retry
        self.back, self.back_label = back, back_label

    def body(self):
        yield Static("[!] operation could not be completed.\n\n" + self.message, classes="spaced error", markup=False)
        yield TerminalMenu([("retry", "retry"), (self.back_label, "back")])

    def leave(self):
        if self.back:
            self.back()
        else:
            self.app.pop_screen()

    def on_key(self, event):
        event.prevent_default()
        if event.key == "escape":
            self.leave()
            event.stop()

    def on_terminal_menu_selected(self, event):
        if event.key == "retry":
            self.app.pop_screen()
            self.retry()
        else:
            self.leave()
