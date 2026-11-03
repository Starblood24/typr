"""Character input and monotonic timing, independent of the terminal UI."""
from dataclasses import dataclass, field
from enum import Enum
from time import monotonic
from typing import Callable


class SessionStatus(Enum):
    READY = "ready"
    RUNNING = "running"
    PAUSE_MENU = "pause_menu"
    FINISHED = "finished"
    ABORTED = "aborted"


@dataclass
class Session:
    target: str
    duration: int | None = 30
    strict: bool = False
    clock: Callable[[], float] = monotonic
    typed: str = ""
    attempts: int = 0
    correct_attempts: int = 0
    started: float | None = None
    ended: float | None = None
    status: SessionStatus = SessionStatus.READY
    samples: list[tuple[float, float]] = field(default_factory=list)
    completed_chars: int = 0
    last_input: float | None = None
    code: bool = False
    automatic: set[int] = field(default_factory=set)

    @property
    def elapsed(self):
        if self.started is None:
            return 0.0
        return max(0.0, (self.ended if self.ended is not None else self.clock()) - self.started)

    @property
    def remaining(self):
        return max(0.0, (self.duration or 0) - self.elapsed)

    @property
    def correct(self):
        return self.completed_chars + sum(a == b for i, (a, b) in enumerate(zip(self.target, self.typed))
                                          if i not in self.automatic)

    @property
    def wpm(self):
        return self.correct / 5 * 60 / self.elapsed if self.elapsed else 0.0

    @property
    def accuracy(self):
        return 100 * self.correct_attempts / self.attempts if self.attempts else 100.0

    @property
    def complete(self):
        return self.typed == self.target if self.strict else len(self.typed) >= len(self.target)

    def type(self, character):
        self.tick()
        if self.status not in (SessionStatus.READY, SessionStatus.RUNNING):
            return
        if len(character) != 1 or not (character.isprintable() or self.code and character == "\n"):
            return
        # Story errors stay visible until backspace; they cannot be bypassed.
        if self.strict and self.typed != self.target[:len(self.typed)]:
            return
        if len(self.typed) >= len(self.target):
            return
        if self.started is None:
            self.started = self.clock()
        self.status = SessionStatus.RUNNING
        self.last_input = self.clock()
        self.attempts += 1
        matched = character == self.target[len(self.typed)]
        self.correct_attempts += matched
        self.typed += character
        if self.code and character == "\n" and matched:
            while len(self.typed) < len(self.target) and self.target[len(self.typed)] == " ":
                self.automatic.add(len(self.typed))
                self.typed += " "

    def backspace(self):
        self.tick()
        if self.status in (SessionStatus.READY, SessionStatus.RUNNING):
            self.last_input = self.clock()
            self.automatic.discard(len(self.typed) - 1)
            self.typed = self.typed[:-1]

    def tick(self):
        if self.status in (SessionStatus.FINISHED, SessionStatus.ABORTED):
            return
        if self.duration is not None and self.started is not None and self.remaining <= 0:
            self.finish(timed=True)
            return
        if self.elapsed >= 1 and (not self.samples or self.elapsed - self.samples[-1][0] >= 1):
            self.samples.append((self.elapsed, self.wpm))

    def finish(self, timed=False):
        if self.status is SessionStatus.FINISHED:
            return
        self.ended = self.started + self.duration if timed and self.started is not None else self.clock()
        self.status = SessionStatus.FINISHED
        elapsed = self.elapsed
        if elapsed >= 1:
            sample = (elapsed, self.wpm)
            if self.samples and self.samples[-1][0] == elapsed:
                self.samples[-1] = sample
            else:
                self.samples.append(sample)

    def next_paragraph(self, target):
        if not self.complete:
            raise ValueError("Cannot advance an unfinished paragraph")
        self.completed_chars += len(self.target)
        self.target, self.typed = target, ""
        self.automatic.clear()

    def pause_menu(self):
        if self.status in (SessionStatus.READY, SessionStatus.RUNNING):
            self.status = SessionStatus.PAUSE_MENU

    def resume(self):
        if self.status is SessionStatus.PAUSE_MENU:
            self.status = SessionStatus.RUNNING if self.started is not None else SessionStatus.READY
