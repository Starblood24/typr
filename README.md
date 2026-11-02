# typr

A quiet, keyboard-first terminal typing utility. Python 3.11+, Textual 8.2.8,
Windows 11 and WezTerm. Soft Phosphor / Old Terminal × Retro Utility.

## Start on this computer

Open WezTerm / PowerShell:

```powershell
cd "$env:USERPROFILE\Desktop\Dev\CLI_Dev\typr"
.\.venv\Scripts\python -m typr
```

On Windows with WezTerm installed, this command and the installed `typr` command
automatically open a separate fullscreen WezTerm window. `./run.ps1` uses the same
launch path. Arguments such as `--skip-boot` and `--data-dir PATH` are forwarded.
Alt+Enter toggles fullscreen with the default WezTerm bindings. The packaged
`assets/wezterm-fullscreen.lua` reuses your terminal configuration without editing
it. Without WezTerm, or on other operating systems, typr runs in the current
terminal. Python packages remain isolated in the local environment.

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
Content is kept within the selected language. Training and Developer are deferred
and do not appear as nonfunctional controls.

Timing starts on the first printable character. Mistakes may be left in place;
Backspace crosses word boundaries. WPM is correct characters divided by five,
per elapsed minute. Accuracy is correct character attempts divided by all
character attempts, so correcting a mistake does not erase it from accuracy.
Backspace itself is not counted as a character attempt. WPM samples use the
same monotonic clock as the session timer. Timed tests supply more text when
needed and retain that complete text for Retry.

Escape opens a dedicated pause menu. **Time continues while paused.** A timed
session automatically completes at its deadline, including while paused.
Settings are also available from Pause; Escape returns to Pause without losing
typed text. Time continues in Settings and its data-management screens too.
Restart is immediate; abort requires confirmation. Completed Classic tests
are saved once. Incomplete, aborted and interrupted tests are discarded.
Retry repeats the same text; New Test keeps settings and generates fresh text.

If saving a completed test or Story paragraph fails, Retry preserves the unsaved
session. Discard Session (including Escape) asks for confirmation; cancelling
returns to the error screen so Retry stays available. Startup storage errors
offer Retry and Quit. Tab and Shift+Tab keep focus in the typing view.

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
to two or one in short windows. The native terminal bar cursor is positioned over the target without inserting a gap, moving the text or recoloring the pending character. WezTerm supports this cursor shape; appearance in other terminals depends on their cursor support. Cursor blinking starts only after input is idle. The boot shows a new status every 0.75 seconds (about 4.5 seconds total) and remains skippable. Artwork visibility depends on available width, not a fixed minimum window height; short windows can scroll the artwork.

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
- `modes/story.py`: validated chapter/paragraph content.
- `storage/database.py`: transactional local persistence.
- `app.py`: one session controller and one timer; lifecycle and screen flow.
- `ui/screens.py`, `ui/widgets.py`, `ui/base.tcss`: keyboard UI and design tokens.
- `assets/`: UTF-8 art, separate language banks and Story JSON content.

The layers are intentionally small: there are no empty service wrappers or
unimplemented mode classes. Training can later record attempts at the engine
boundary, and Developer can supply snippet content to the shared typing view;
indentation accounting and multiline editing belong to that later implementation.
They are not claimed as working features in this MVP.

The supplied 24-line Braille star is unchanged and guarded by a SHA-256 test.
The Compact Utility wordmark is used on Home only; the star is used at boot only.
