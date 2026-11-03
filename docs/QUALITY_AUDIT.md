What this repo does: typr is a local keyboard typing app with Classic, Developer and Story sessions. It stores settings, completed tests and Story checkpoints in SQLite. This audit assumes one person typing in one app, with occasional database/file errors and terminal resizing.

The audit read the entry points, all application modules, assets, build configuration, README and tests. Reproduction tests ran outside the project before production changes: seven failed assertions across four functional findings. Escape on Results was also checked and passed; it is not reported as a bug.

**Must fix:**

1. **Content errors can close the app** (`src/typr/app.py`, `modes/classic.py`, `modes/developer.py`, `modes/story.py`).
   - **What this is:** These paths load words, code and stories before starting or extending a session.
   - **Problem:** A missing word bank raises OSError outside the error-dialog path. Empty banks raise IndexError; a malformed Story chapter raises AttributeError. Retry is unavailable.
   - **Fix:** Validate the loaded structures and route content loading through the existing recoverable operation handler. Commit new session state only after loading succeeds.
   - **If we skip it:** Damaged or incomplete assets can crash startup of a test and lose the current flow.

2. **The session timer reads widgets during shutdown** (`src/typr/app.py:tick`).
   - **What this is:** A periodic callback refreshes typing metrics and checks the deadline.
   - **Problem:** The callback still runs after Textual marks the app stopped and starts removing screen children. A Story screen without its removed header raises NoMatches. This reproduces a previously observed test failure.
   - **Fix:** Stop processing the callback when the app is no longer running.
   - **If we skip it:** Closing the app can show a traceback, and UI tests can fail during cleanup.

**Should fix:**

3. **Resizing replaces the quit prompt shortcuts** (`src/typr/ui/screens.py:HomeScreen`, `UtilityScreen.responsive`).
   - **What this is:** The footer explains which keys work in the current screen.
   - **Problem:** Open the terminate prompt, then resize the terminal. The footer shows menu navigation while the prompt still expects confirmation.
   - **Fix:** Derive the Home footer from its actual confirmation state and reuse that value everywhere.
   - **If we skip it:** The visible controls disagree with what the keyboard does.

4. **Settings accept another setting's values** (`src/typr/app.py:initialize`).
   - **What this is:** Saved preferences are read on launch.
   - **Problem:** `ascii art=subtle` and `animations=on` are accepted even though neither is a valid choice for that setting.
   - **Fix:** Define the allowed choices once per setting and use them for both loading and changing preferences.
   - **If we skip it:** Damaged preferences appear as unsupported choices and behave inconsistently.

5. **Keyboard rules and an unused generation option are duplicated** (`src/typr/ui/screens.py`, `modes/classic.py`).
   - **What this is:** Textual dispatches inherited handlers, and the app already owns the priority Ctrl+R binding.
   - **Problem:** Three screens suppress inherited handling, then forward keys to the base handler by hand. TypingScreen repeats the global restart action. The `count` override has no caller; two screen imports are unused.
   - **Fix:** Allow native inherited handling for unhandled keys and keep the global restart binding. Remove the unused override and imports. Do not suppress inherited handling for Escape.
   - **If we skip it:** Changes to navigation or restart have redundant paths to maintain.

6. **Version strings have three sources** (`pyproject.toml`, `src/typr/__init__.py`, `ui/screens.py`).
   - **What this is:** Package metadata and the Home/Pause header identify the installed release.
   - **Problem:** Bumping only the package version leaves the displayed version at 0.1.0.
   - **Fix:** Use the existing `__version__` for runtime display and setuptools metadata.
   - **If we skip it:** Future releases can report the wrong version, making bug reports unreliable.

Verdict: Fix content error handling and shutdown first, then remove the confirmed duplication.

Lean: about 13 redundant lines and 0 dependencies can be removed; necessary validation adds a small amount of code.

Not checked: native Linux/macOS, public package publication, TypeScript/Rust compilation and every possible terminal. Git diff commands failed in the host; before/after snapshots are used for the follow-up change review. No security vulnerability was confirmed by this audit.
