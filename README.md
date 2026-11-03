# typr

A quiet, keyboard-first terminal typing utility. Python 3.11+, Textual 8.2.8,
Windows 11 and WezTerm. Soft Phosphor / Old Terminal × Retro Utility.

## Start on this computer

Open WezTerm / PowerShell:

```powershell
cd "$env:USERPROFILE\Desktop\Dev\CLI_Dev\typr"
.\.venv\Scripts\python -m typr
```

The Python command, installed `typr` command and `./run.ps1` share one startup
path. An identified WezTerm or Windows Terminal opens a new fullscreen window
of the same terminal. Startup inside kitty on Linux/macOS uses its fullscreen
launch option. A classic Windows console (Command Prompt or PowerShell in
Console Host) switches its existing window to fullscreen using the native console
API and restores its previous display mode on normal process exit. An already
fullscreen console stays fullscreen. Windows Terminal is also recognized when
Windows delegates a cmd/PowerShell session without setting WT_SESSION: typr checks
the actual owning terminal window. A real classic console takes precedence
over inherited terminal identifiers and fullscreen launch markers; SSH and nested
sessions still stay in place. An installed terminal alone never causes
typr to switch to it.

Use `typr --windowed` (or `python -m typr --windowed`) to keep the current
window and its display mode. Unknown terminals, SSH, tmux/screen and redirected input/output stay
in place automatically. If a fullscreen launcher is missing or reports failure,
typr falls back to the current terminal. Arguments, Python environment and working
directory are preserved; global terminal settings are not edited.

Windows Terminal and WezTerm were exercised in real Windows windows. The Linux
and macOS WezTerm/kitty paths have automated launcher tests only; they still need
native system verification. GNOME Terminal, iTerm2 and Terminal.app currently use
the existing window; automatic fullscreen is not implemented for them.

## Install elsewhere

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[test]"
.\.venv\Scripts\python -m typr
```

An installed `typr` command is also available inside the virtual environment.
No network connection is needed after installation. The decorative Classic
command preview is never sent to a shell.

## Classic

Quick Start always uses Standard / English / Common / 30 seconds.
Classic Setup remembers its own last configuration. Setup supports English and
German; Common, Mixed and Advanced; 15/30/60/120 seconds or 10/25/50/100 words.
Content is kept within the selected language. Training remains deferred.

Timing starts on the first printable character. Mistakes may be left in place;
Backspace crosses word boundaries. WPM is correct characters divided by five,
per elapsed minute. Accuracy is correct character attempts divided by all
character attempts, so correcting a mistake does not erase it from accuracy.
Backspace itself is not counted as a character attempt. WPM samples use the
same monotonic clock as the session timer. Chart recording begins only after a
full second, avoiding a startup spike from dividing by a few milliseconds. Sessions
shorter than one second have no chart samples. During typing, only time and accuracy
are shown; WPM remains on the results screen. Timed tests supply more text when
needed and retain that complete text for Retry.

Escape opens a dedicated pause menu. **Time continues while paused.** A timed
session automatically completes at its deadline, including while paused.
Settings are also available from Pause; Escape returns to Pause without losing
typed text. Time continues in Settings and its data-management screens too.
Restart is immediate; abort requires confirmation. Completed Classic tests
are saved once. Incomplete, aborted and interrupted tests are discarded.
Retry repeats the same text; New Test keeps settings and generates fresh text.
The results chart has a fixed 20–100 WPM scale in steps of 10. Values outside
that range are drawn at the nearest chart edge; session metrics retain their values.

Unreadable or malformed word banks, snippets and stories open the error screen
with a Retry action. Failed New Test loading preserves the previous saved result.

If saving a completed test or Story paragraph fails, Retry preserves the unsaved
session. Discard Session (including Escape) asks for confirmation; cancelling
returns to the error screen so Retry stays available. Startup storage errors
offer Retry and Quit. Tab and Shift+Tab keep focus in the typing view.

## Developer

Open Classic and change `mode` to `developer`. Choose Python, JavaScript,
TypeScript or Rust, then a complete-snippet test or a 15/30/60/120-second test.
There are three complete snippets per language. Word counts and vocabulary
difficulty are not shown for code. The command preview remains decorative.

Enter types a newline. After a matching newline, the next target line's leading
spaces are inserted automatically. Backspace removes them one space at a time,
and can cross previous line boundaries. Automatically inserted spaces contribute
neither WPM nor accuracy attempts; spaces you type manually after deleting them
do count. Manually typed newlines count as one character attempt.

The code viewport preserves indentation and blank lines, wraps long lines without
discarding text and follows the cursor. No whitespace markers or extra input field
are used. Code is typing material and is never executed by typr.

Pause, restart, results and local history use the Classic session flow. Retry
preserves the exact text; New Test chooses another snippet. Timed tests append
whole snippets when necessary. Completed Developer sessions appear in Classic
statistics with their programming language. Quick Start always stays Standard /
English / Common / 30 seconds, even after using Developer.

## Story

Three original stories (English and German), 11 chapters and 22 paragraphs of
40–80 words, with unique illustrations at selected chapter transitions.
Filter the directory with Left/Right. Enter starts or resumes the selected story.
The separate `restart selected story` action requires confirmation.

Errors must be corrected with Backspace before typing can continue. Completed
paragraphs advance immediately, without Enter, and are saved transactionally.
They cannot be edited. Chapter introductions mark selected important transitions. Interrupted
paragraphs restart from their beginning on the next launch; there is no recovery
prompt. A completed story remains marked complete until explicitly restarted.
Story results do not enter the Classic statistics page.

## Keys

| Key | Action |
| --- | --- |
| Up / Down | Menu selection; scroll statistics |
| Left / Right | Change a setting or Story language filter |
| Enter | Select |
| Escape | Home quit request; back; typing pause; resume from pause |
| Backspace | Delete typed character |
| Ctrl+R | Restart current test / current unfinished Story paragraph |
| Ctrl+C | Request quit confirmation |
| q | Quit request on Home only |

Quit uses `y` to confirm; `n`, Enter and Escape cancel. Paste is ignored during
typing so pasted content cannot create a measured result.

## Settings and data

Only Animations, Cursor Blink, ASCII Art and Data Management are exposed.
Changes autosave. ASCII Art Off also activates Compact Utility Mode, retaining
boot text and all functionality. Small windows automatically compact; below
40 × 12 the application asks for a resize. Typing uses three lines, reducing
to two or one in short windows. The native terminal bar cursor is positioned over the target without inserting a gap, moving the text or recoloring the pending character. WezTerm supports this cursor shape; appearance in other terminals depends on their cursor support. Cursor blinking starts only after input is idle. During screen painting the cursor is hidden, then restored at the typing position before the frame completes, preventing a visible cursor at intermediate drawing positions. The boot shows a new status every 0.75 seconds (about 4.5 seconds total) and remains skippable. Artwork visibility depends on available width, not a fixed minimum window height; short windows can scroll the artwork.

Data is local SQLite at `%LOCALAPPDATA%\typr\typr.db` on Windows (the precise
path is shown under Settings → Data). Settings, last Classic configuration,
completed Classic history and the next unfinished Story paragraph share SQLite
transactions; no separate configuration file is necessary. Data reset requires
confirmation and removes history, progress and saved preferences.

Use `--data-dir PATH` for a separate profile or `--skip-boot` to bypass the intro.
Back up the database while typr is closed. No telemetry or cloud storage.

Textual/Rich detects terminal color support and downgrades output for ANSI
terminals. WezTerm supports the exact RGB palette. To diagnose other terminals,
`$env:TEXTUAL_COLOR_SYSTEM = 'standard'` forces the ANSI output path for one shell.

## Tests

```powershell
.\.venv\Scripts\python -m pytest -q
```

Tests cover input, German Unicode, corrections, timing, paused expiry, all Classic
configurations, persistence, Story progress/restart, keyboard navigation, resize,
settings, retry and error dialogs. Test data uses temporary directories.
`docs/VALIDATION.md` records the final run and visual verification.

## Code map and future work

- `core/typing_engine.py`: terminal-independent input, timing and metrics.
- `modes/classic.py`: validated Classic configuration and word generation.
- `modes/developer.py`: bundled code-snippet selection.
- `modes/story.py`: validated chapter/paragraph content.
- `storage/database.py`: transactional local persistence.
- `app.py`: one session controller and one timer; lifecycle and screen flow.
- `ui/screens.py`, `ui/widgets.py`, `ui/base.tcss`: keyboard UI and design tokens.
- `assets/`: UTF-8 art, separate language banks and Story JSON content.

The layers are intentionally small: there are no empty service wrappers or
unimplemented mode classes. Training can later record attempts at the engine
boundary. Developer reuses that engine with multiline input and explicit
auto-indentation accounting; snippets live in assets/code/snippets.json.

The supplied 24-line Braille star is unchanged and guarded by a SHA-256 test.
The Compact Utility wordmark is used on Home only; the star is used at boot only.
