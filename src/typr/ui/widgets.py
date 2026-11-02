from importlib.resources import files
import math

from rich.cells import cell_len
from rich.text import Text
from textual import events
from textual.message import Message
from textual.widgets import Static
from textual.widget import Widget
from textual.geometry import Offset

PALETTE = {"background": "#0B130E", "primary": "#91B99A", "correct": "#A9D6B1",
           "pending": "#4C6652", "muted": "#63816A", "separator": "#294330",
           "focus": "#C1E3C7", "error_background": "#764E4E", "error_text": "#F1C1B8"}


def art(name):
    return files("typr").joinpath(f"assets/art/{name}.txt").read_text(encoding="utf-8")


def progress(fraction, width=20):
    fraction = min(1, max(0, fraction))
    filled = int(fraction * width)
    return f"[{'#' * filled}{'-' * (width-filled)}] {fraction:.0%}"


def clock_text(seconds):
    seconds = max(0, math.ceil(seconds))
    return f"{seconds // 60:02}:{seconds % 60:02}"


def wpm_chart(samples, width=40, height=6):
    if not samples:
        return "WPM OVER TIME\n\n(no samples)"
    duration = max(samples[-1][0], 1)
    top = max(10, math.ceil(max(w for _, w in samples) / 10) * 10)
    grid = [[" " for _ in range(width)] for _ in range(height)]
    previous = None
    for second, wpm in samples:
        x = min(width - 1, int(second / duration * (width - 1)))
        y = height - 1 - min(height - 1, round(wpm / top * (height - 1)))
        if previous:
            px, py = previous
            for xx in range(px, x + 1):
                yy = round(py + (y - py) * (xx - px) / max(1, x - px))
                grid[yy][xx] = "*"
        grid[y][x] = "*"
        previous = x, y
    lines = ["WPM OVER TIME", ""]
    for y, row in enumerate(grid):
        lines.append(f"{round(top * (height-1-y)/(height-1)):3} |" + "".join(row))
    lines.extend(["    +" + "-" * width, "     0" + f"{duration:.0f}s".rjust(width - 1)])
    return "\n".join(lines)


class TerminalMenu(Widget, can_focus=True):
    class Selected(Message):
        def __init__(self, key):
            super().__init__()
            self.key = key

    class Changed(Message):
        pass

    def __init__(self, options, **kwargs):
        super().__init__(**kwargs)
        self.options = options
        self.index = next((i for i, (_, key) in enumerate(options) if key is not None), 0)

    @property
    def selected(self):
        return self.options[self.index][1] if self.options else None

    def compose(self):
        for label, _ in self.options:
            yield Static(label, markup=False, classes="menu-row")

    def on_mount(self):
        self.paint()
        self.focus()

    def paint(self):
        for i, row in enumerate(self.children):
            label, key = self.options[i]
            row.update(("> " if i == self.index else "  ") + label)
            row.set_class(i == self.index, "selected")
            row.set_class(key is None, "section")
        if self.children:
            self.children[self.index].scroll_visible(animate=False)

    def relabel(self, options):
        if len(options) != len(self.options):
            raise ValueError("Menu length changed")
        self.options = options
        self.paint()

    def on_key(self, event: events.Key):
        if event.key in ("up", "down") and self.options:
            step = 1 if event.key == "down" else -1
            for _ in self.options:
                self.index = (self.index + step) % len(self.options)
                if self.options[self.index][1] is not None:
                    break
            self.paint()
            if self.app.settings.get("animations") == "subtle":
                self.children[self.index].styles.text_style = "bold"
                self.set_timer(.12, self.end_pulse)
            self.post_message(self.Changed())
            event.stop()
        elif event.key == "enter" and self.selected is not None:
            self.post_message(self.Selected(self.selected))
            event.stop()

    def end_pulse(self):
        for row in self.children:
            row.styles.text_style = "none"


class TypingView(Widget, can_focus=True):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.blink = True
        self.caret_offset = Offset(0, 0)

    def render(self):
        session = self.app.session
        if session is None:
            return Text("")
        width = max(2, self.size.width)
        text = session.target
        lines, start = [], 0
        while start < len(text):
            end, cells = start, 0
            while end < len(text) and cells + cell_len(text[end]) <= width:
                cells += cell_len(text[end])
                end += 1
            if end < len(text):
                space = text.rfind(" ", start, end)
                if space > start:
                    end = space + 1
            end = max(start + 1, end)
            lines.append((start, end))
            start = end
        cursor = len(session.typed)
        first = next((i for i, (_, end) in enumerate(lines) if cursor < end), max(0, len(lines)-1))
        if lines:
            self.caret_offset = Offset(cell_len(text[lines[first][0]:cursor]), 0)
        result = Text()
        visible_lines = max(1, min(3, self.size.height))
        for row, (begin, end) in enumerate(lines[first:first+visible_lines]):
            if row:
                result.append("\n")
            for i in range(begin, end):
                style = PALETTE["pending"]
                if i < cursor:
                    style = PALETTE["correct"] if session.typed[i] == text[i] else f'{PALETTE["error_text"]} on {PALETTE["error_background"]}'
                result.append(text[i], style=style)
        return result

    def on_key(self, event: events.Key):
        if self.app.saving:
            event.stop()
            return
        if event.key == "backspace":
            self.app.session.backspace()
        elif event.character and event.character.isprintable():
            self.app.session.type(event.character)
        else:
            return
        self.blink = True
        self.app.after_input()
        self.refresh()
        event.stop()
        event.prevent_default()

    def on_paste(self, event: events.Paste):
        # Pasting would invalidate typing measurements.
        event.stop()
        event.prevent_default()
