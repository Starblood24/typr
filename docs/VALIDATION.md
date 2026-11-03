# typr 0.1.0 — validation

Verified on 1 November 2026, Windows 11, Python 3.11.0, Textual 8.2.8.

## Final installed-project test run

Project: `C:\Users\emir0\Desktop\Dev\CLI_Dev\typr`

```text
71 passed in 8.64s
```

The final run used the Desktop project's isolated Python environment and tested
the installed project source. An earlier independent working-copy run also passed.

## Coverage

| Area | Verified behavior |
| --- | --- |
| Input | Correct/error/pending rendering, German Unicode, free correction, cross-word Backspace, paste rejected |
| Timer | First-input start, monotonic measurement, pause continues time, expiry from Pause, final sample bounded by duration |
| Classic | All 48 language/difficulty/type/length configurations; invalid configurations rejected |
| Results | WPM/accuracy/duration, ASCII graph, identical Retry, fresh New Test, no duplicate save |
| Storage | Completed sessions only, SQLite round-trip, settings autosave, last-used configuration, confirmed reset |
| Story | Strict correction, immediate paragraph advance, locked completed paragraphs, checkpoint persistence, direct mid-chapter resume, complete Story flow, restart confirmation |
| Navigation | Boot skip and automatic finish, Home selection preserved, setup, pause/resume/abort, stats, settings, errors/retry, quit cancellation, global Ctrl+R |
| Responsive | 120×40, 80×24, 60×18, 40×12 and 32×10; cursor viewport and compaction; tiny-window resize hint |
| Assets | Exact 24-line star hash; separate language banks; three original stories; 22 paragraphs of 40–80 words; unique 6–10-line chapter illustrations |

Star SHA-256 (UTF-8 with final newline):

```text
1264138360dc75c1f249add9e9a2a1ca95ee1170a62c100fee6a6376ced5871d
```

## Visual and terminal checks

Real Textual renders were exported and visually inspected for Home, starOS,
Classic Typing, Results and 40×12 Story Typing. Additional renders were generated
for setup, pause, directory, chapter introduction, Story typing and compact Home.
The small Story layout was corrected so its metrics, typing position and progress
remain visible together. Soft Phosphor colors were checked with `NO_COLOR` absent;
the application still respects a user's `NO_COLOR` preference.

A real WezTerm instance ran typr. Its own pane was read through WezTerm's CLI;
Quick Start, character input, Pause and automatic timed transition to Results
were verified. Windows GUI screenshot access did not expose that window, so this
was a terminal-content check rather than a native-window screenshot review.
Terminal font appearance depends on the user's WezTerm font.

The ANSI fallback was forced with `TEXTUAL_COLOR_SYSTEM=standard` and the
application's console confirmed standard-color output. No separate physical
ANSI-only terminal was available for visual inspection.

The installable wheel was built successfully; its manifest includes every runtime
Python module, both artwork files, both language banks, three Story files and CSS.

## Intentional limits

- Developer and Training are deferred as requested; no inactive menu items.
- No endurance or high-volume database benchmark was run for this local MVP.
- No model switch occurred. This running chat exposes no supported model-switch
  control; the requested economical-model-to-Astra sequence could not be applied.
- Existing Desktop projects were preserved. Creation refused an existing `typr`
  target, and only the newly created project's files were subsequently updated.

## Follow-up fixes — 1 November 2026

Boot status cadence increased to 0.75 seconds, approximately 4.5 seconds total.
Artwork is now hidden only for insufficient width or the explicit ASCII Art Off
setting, rather than automatically in windows with fewer than 30 rows. The cursor
underlines the current target cell instead of inserting an extra character.

Full regression suite: **74 passed in 11.24s**. New tests verify stable target
characters/positions while typing, deleting and blinking; artwork at 120×24 and
120×40, narrow fallback and explicit disable; readable intermediate boot status
and skipping. A final UI-only run also verifies measurement from original art.
No new manual WezTerm session was performed for these follow-up fixes.

## Native bar cursor — 2 November 2026

The underline is replaced by the native terminal bar cursor. Target rendering
contains only target characters and retains pending colors at the caret. Cursor
placement uses terminal-cell widths and follows wrapping/resizing. It is solid
during typing, follows the idle-blink preference, and is hidden in other screens.
The default cursor style is restored on exit. The display hook is tied to the
pinned Textual 8.2.8 version and must be reviewed when upgrading Textual.

**75 tests passed in 11.88s.** A real isolated WezTerm test reported a visible
`SteadyBar` before and after input. Its position advanced from `(1,3)` to `(2,3)`
while all three target lines remained byte-for-byte unchanged. Other terminal
emulators were not manually tested.

## Audit and review fixes — 2 November 2026

All five audit/review findings are addressed. Failed Classic saves and Story
checkpoints retain Retry and require explicit confirmation to discard; cancelling
keeps the pending save accessible. Startup errors provide Retry/Quit instead of
returning to an empty screen. Tab/Shift+Tab no longer steal typing focus. Common
screen setup runs once through Textual event dispatch.

A recording-driver test checks native cursor writes and flushes, cursor hiding
on Pause, idle visibility changes and default-style restoration on exit.

**85 tests passed in 15.79s.** New regression cases cover both save types with
retry/discard, cancelling discard and rejecting a restart bypass; startup retry,
quit and Escape; typing focus across pause/resume; and single screen setup.
No new manual WezTerm session, other-OS run or endurance test was performed.

## Fullscreen starter — 2 November 2026

run.ps1 launches a separate WezTerm instance with project-local configuration.
The native fullscreen API was checked in a real window: is_full_screen=true,
2880×1800, inherited font size 14. A hash check confirmed the original user
configuration was unchanged. The Lua self-check verifies enabling fullscreen,
not disabling it on reattachment and leaving other workspaces untouched.

Run the self-check with `wezterm --config-file tests/check_fullscreen.lua show-keys`.
The Python application is unchanged; the previously passing 85 Python tests were
not repeated for this launcher-only change. Other terminal emulators are not
supported by this Windows/WezTerm fullscreen starter.

## Fixed boot progress position — 2 November 2026

The boot log now reserves four lines and displays status messages on consecutive
rows. Progress and readiness have a separate bottom-docked status area, anchored
to the right-hand boot column. Short windows reduce the column height to fit.

**88 tests passed in 17.13s.** Added checks keep the progress coordinates constant
through all five animation stages at 100×36, 100×24 and 40×12. Both normal and
compact rendered views were visually inspected. No new native WezTerm session
was run for this layout-only change.

## Escape on Home — 2 November 2026

Escape now opens the same inline terminate prompt as q. In that prompt, y
quits; n, Enter and Escape cancel and preserve the menu selection. The Home
footer lists q/esc. Four keyboard regression cases verify these choices.

**92 tests passed.** No additional manual WezTerm session was run.

## Fixed Quick Start defaults and Pause settings — 2 November 2026

Quick Start always starts English / Common / time / 30 seconds, independently
of saved Classic Setup preferences. Active session configuration is used for
text replenishment, history, restart, Retry and New Test. Pause opens the existing
Settings screen; returning preserves the session and selection. Timed expiry
clears nested Settings, Data and confirmation screens before showing Results.

**97 tests passed in 24.62s.** Regression checks cover saved non-default Classic
settings, Quick Start retries and history, Classic/Story settings round trips,
and timed expiry at each settings depth. No new manual WezTerm session was run.

## Fullscreen from the Python command — 2 November 2026

The direct Python command and installed entry point now launch fullscreen
WezTerm on Windows too. run.ps1 delegates to this same path. A child-only
environment marker prevents recursive launches. Arguments and the working
directory are preserved; missing WezTerm and other platforms use the existing
terminal. The Lua configuration is included in the installable Python package.

**101 tests passed in 22.60s.** Four launcher checks cover argument forwarding,
recursion prevention, unsupported environments and parent exit status. The Lua
fullscreen self-check passed. A real direct Python launch reported fullscreen=true,
2880 x 1800, inherited font size 14. The global user configuration hash was unchanged.

## Terminal-aware fullscreen startup — 2 November 2026

Shared terminal.py now detects the host and launches that terminal, preserving
Python, arguments, working directory and user configuration. Added --windowed;
unknown terminals, SSH, tmux/screen and redirected streams stay in place. Child
arguments and an environment marker prevent recursion. Missing executables,
OS launch errors and nonzero launcher status fall back to the current terminal.

**125 tests passed in 23.43s.** Tests cover terminal precedence/inherited markers,
Windows/Linux/macOS command selection, remote/nested sessions, failure paths,
argument forwarding and explicit windowed startup. The Lua self-check passed.
Real Windows Terminal and WezTerm launches reached Home using data directories
with spaces and an umlaut. Native test-window bounds matched the display with
no caption (1440 x 900 logical pixels on the 2880 x 1800 display). User WezTerm
configuration SHA-256 remained unchanged. Test apps exit themselves.

Linux/macOS and kitty were not run natively. GNOME Terminal, iTerm2 and
Terminal.app have no automatic fullscreen launcher in this change.

## Classic Command Prompt fullscreen — 2 November 2026

A visible legacy console is now recognized after named terminal detection.
Hidden ConPTY message windows are excluded. The native console display-mode API
enables fullscreen in place; normal interpreter exit restores windowed mode only
if typr changed it. Existing fullscreen state and --windowed are preserved.

**130 tests passed in 29.95s.** Five additional cases cover legacy-host detection,
restoration after success, existing fullscreen and failed query/set operations.
A real conhost.exe + cmd.exe launch reached Home at display mode 1, 1440 x 900
logical pixels, and restored mode 0 at exit. The --windowed run reached Home at
mode 0 in its original 930 x 516 window. Native check files use isolated data.
Force-killing the process cannot guarantee restoration. Linux/macOS were not rerun.

## cmd fullscreen and cursor rendering regression — 2 November 2026

Reproduced a classic-console launch that stayed windowed when TERM_PROGRAM,
WEZTERM_PANE and TYPR_FULLSCREEN were inherited from a parent terminal. The
visible console now wins over those markers; remote/nested sessions remain excluded.
Native before/after checks covered the actual boot and typing screens: the failing
case stayed at mode 0 before the fix, then reached mode 1 and full display bounds
after it. Exit restored the original 930 x 516 window.

Captured the real output stream while typing. Previously the caret remained
visible while Textual moved its output position and repainted metrics/text. Cursor
visibility now brackets rendering inside Textual update boundaries: hide, paint,
position/show, finish update. No target characters or wrapping are changed.

**133 tests passed in the full run (46.80s).** After adding synchronized-output
coverage, **36 targeted cases passed (2.45s)**, bringing covered cases to 134.
The cursor regression now uses the real App._display implementation rather than
mocking away the frame rendering. Native console output ordering was checked;
no pixel/video-based flicker measurement or Linux/macOS run was performed.

## Windows default-terminal delegation — 2 November 2026

Reproduced the remaining failure using the normal Windows launch path for both
cmd.exe and Windows PowerShell, without forcing conhost.exe. Windows Terminal
1.24 hosted both sessions, but WT_SESSION was absent. GetConsoleWindow returned
a zero-size PseudoConsoleWindow with IsWindowVisible=true. Its owner process was
the shell, so neither visibility nor process-name guessing identifies this host.

Legacy fullscreen now requires ConsoleWindowClass. For delegated sessions,
GetAncestor(GetConsoleWindow(), GA_ROOTOWNER) identifies the actual
CASCADIA_HOSTING_WINDOW_CLASS window and selects the existing Windows Terminal
fullscreen launcher. Unknown hosts remain in place. No process enumeration,
global terminal-setting changes or extra dependencies are used.

**142 tests passed in 40.54s.** Eight new cases cover real versus pseudo window
classes, delegated/unknown window ownership and startup without terminal markers.
An earlier full run overlapped native diagnostics and had two UI timing failures;
the final standalone full run passed.

Real normal cmd and PowerShell launches were recorded before and after the fix.
Before: 1186 x 618 logical pixels with a caption. After: each reached BootScreen
in a new Windows Terminal window at 1440 x 900 logical pixels, matching the
display with no caption. Arguments and the same editable Python installation
were confirmed. Native check logs are kept in workspace work/host-debug.
Linux/macOS were not tested for this Windows-only correction.

## Developer mode — 2 November 2026

Developer is a Classic content selection, with 12 complete snippets across Python,
JavaScript, TypeScript and Rust. Sessions may finish a snippet or use a time limit.
Auto-indent follows matching target newlines, supports single-space deletion and
is excluded from WPM/accuracy. The shared renderer preserves code line structure
and keeps the caret visible through wrapping and resizing. Retry, New Test,
Quick Start defaults, old settings and completed-session persistence were covered.

**162 automated cases passed.** Phase checks: 64 content/core cases, 67 after
engine changes, and 20 Developer-specific cases after UI integration. Python
snippets were parsed with ast; all JavaScript snippets passed node --check.
TypeScript/Rust compilers are absent, so those snippets were not compiler-checked.

Native Developer TypingScreen checks after real cmd, PowerShell and WezTerm
starts reported code=true and fullscreen windows matching the display, without
a caption (1440 x 900 logical pixels). WezTerm also reported is_full_screen=true
at 2880 x 1800 pixels. SHA-256 checks confirm terminal.py, cli.py, the Lua starter
and run.ps1 are unchanged. Code views at 100 x 36 and 40 x 12 were visually
inspected. Native Linux/macOS verification remains pending.

## Fixed WPM chart scale — 2 November 2026

Results now use six fixed levels: 120, 100, 80, 60, 40 and 20 WPM. Samples
outside the range are clamped to the chart edge without modifying session
metrics. Added coverage for beginner speeds and large startup peaks.

**101 targeted tests passed in 2.19s:** core/chart, results flow and terminal
regressions. The rendered text chart was inspected. No native GUI rerun.

## WPM chart refinement — 2 November 2026

The fixed chart now spans 20 to 100 WPM with nine levels, every 10 WPM.
Out-of-range samples remain clamped to the chart edge.
**59 targeted core/chart and results-flow tests passed in 1.93s.**
No native terminal rerun for this chart-only adjustment.

## WPM startup sampling and focus — 2 November 2026

The first graph sample previously used the first tick after input, even at a
near-zero elapsed time. Sampling now requires at least one second, with the
existing one-second cadence thereafter. Final samples use actual elapsed time
and replace an existing same-timestamp sample. Subsecond tests have no chart
points. Cumulative final WPM and actual timestamps are preserved.

Removed live WPM from the shared Classic/Developer/Story metrics row; time and
accuracy remain. Results retain WPM. Regression cases cover the startup spike,
short sessions, final-sample correctness and all three typing modes.
**171 tests passed.** No additional native terminal run for this metrics change.

## Ponytail audit and follow-up review — 2 November 2026

Six findings were addressed: recoverable content-loading errors and validation;
shutdown timer safety; quit-footer resize state; per-setting validation; redundant
keyboard/generation paths; and one shared version source. The audit reproduced
seven failing cases before fixes. Results Escape was checked and already correct.

The follow-up review also checked inherited Escape handling and saved-result
preservation when New Test fails. Added 18 regression cases. **189 tests passed
in the final full run.** The production diff adds 64 lines and removes 39, with
no new dependencies. Required validation accounts for most added code.

Real cmd, PowerShell and WezTerm launches reached Developer TypingScreen in
fullscreen. Windows measurements matched the display without a caption; WezTerm
reported 2880 x 1800 and is_full_screen=true. Protected startup-file hashes are
unchanged. Public package services, native Linux/macOS and TypeScript/Rust
compilation were not exercised. Full reports are in QUALITY_AUDIT.md and
QUALITY_REVIEW.md.
