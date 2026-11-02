# Approved design contract

Source: the user's complete specification supplied in this chat, following the
23-stage design review, 1 November 2026. The implementation keeps these decisions:

- English interface; Old Terminal × Retro Utility; exact Soft Phosphor tokens.
- Left alignment, thin separators, compact outer spacing, persistent contextual
  footer. No cards, graphical buttons, full-screen border or theme selector.
- Original 24-line Braille star at boot only. UTF-8 whitespace is preserved.
  Approximate 4.5-second skippable starOS introduction; compact keeps boot text.
- Compact Utility logo left of the six-item Home menu. No Quick Start preview.
  Version appears only on Home and Pause. Returning preserves menu selection.
- First launch goes directly to Home. Quick Start defaults to English / Common /
  30 seconds and later reuses the most recently started Classic configuration.
- Classic has CONTENT and SESSION groups and a decorative command preview.
  Standard only; en/de; Common/Mixed/Advanced; time 15/30/60/120; words 10/25/50/100.
- Shared typing view: integrated text, distinct correct/error/pending treatment,
  native thin bar cursor independent of target characters; solid while active, slow idle blink. Three lines, reduced
  on small windows, with the cursor always in the visible section. No whitespace
  marks or separate input box. Ordinary Backspace crosses word boundaries.
- Monotonic first-keystroke timing; pause screen suspends input, not time.
  Expiry opens Results even from Pause. Restart is immediate; Abort confirms.
- Results: WPM, accuracy, duration and a small ASCII WPM chart. Retry repeats the
  same text; New Test changes content with identical settings. No raw WPM, badges,
  weak-word table, celebratory animation or extra dashboard.
- Mixed-language Story directory with language filter and selected-story progress.
  Enter continues directly. Explicit Story restart requires confirmation.
- Original short Story paragraphs (40–80 words), chapter metadata and distinct
  illustrations at selected transitions. No illustration in the typing view.
- Strict Story correction; immediate paragraph transitions; transactional autosave
  per complete paragraph; completed paragraphs cannot be edited. Interruption
  resumes at the first unfinished paragraph with no recovery prompt.
- Stats contain completed Classic sessions only. No Story stats or analytics graph.
- Settings: Animations, Cursor Blink, ASCII Art, Data. Autosave. ASCII Off also
  compacts spacing. Data path is visible; destructive reset requires confirmation.
- Home quit confirmation is inline. y confirms; n/Enter/Escape cancel. A short
  goodbye returns to the shell. Ctrl+C requests confirmation; Ctrl+R restarts.
- Keyboard scheme: arrows, Enter, Escape, q on Home, Ctrl+R and Ctrl+C. No Vim,
  numeric shortcuts, Ctrl+Backspace, Tab-to-restart or separate Help screen.
- Sequential boot, brief selection pulse, restrained dim transitions; immediate
  paragraph switch, static results and settings updates. Animations can be disabled.
- Small-window compaction and scrolling; a resize hint only below 40 × 12.
  Textual/Rich measures terminal cells and negotiates terminal color support.
- Local SQLite holds settings, last Classic configuration, completed tests and
  Story checkpoints. No incomplete Classic history, telemetry or cloud dependency.
- Developer (Python/JS/TS/Rust, preserved snippets, auto-indent accounting) and
  Training remain deferred. Core, content, persistence and UI stay separate so
  those modes can later reuse the same typing/session boundary.

The suggested architecture is consolidated into substantive modules rather than
empty one-method service/repository wrappers. App owns the single session timer
and transitions; the core can be tested without Textual. SQLite provides atomic
configuration updates, so no second TOML persistence mechanism is added.
