# Developer mode implementation

1. Add backwards-compatible Classic configuration and complete Python, JavaScript,
   TypeScript and Rust snippets. Developer supports timed tests or a full snippet.
2. Extend the shared Session with multiline input and removable auto-indentation.
   Track automatically inserted positions so they never contribute to WPM or accuracy.
3. Integrate the Classic setup, code viewport, results/retry/new test and persistence.
   Preserve Quick Start's fixed English/Common/30s settings and Story behavior.
4. Test the core, all language flows, wrapping/cursor, persistence and terminal launchers.
   Verify real cmd, PowerShell and WezTerm fullscreen starts. Confirm startup files
   match their pre-change SHA-256 hashes. Build and inspect the installable package.

Auto-indent follows the next target line's exact leading spaces after a matching
newline. Backspace removes one character at a time. Code is typing material only.
Training remains deferred. Existing UI palette, menu and cursor rendering stay in use.

## Completed verification

All four steps completed. 162 automated cases passed. Python snippets passed AST
parsing; JavaScript snippets passed node --check. TypeScript and Rust were not
compiler-checked because those compilers are not installed. Code screenshots
were inspected at 100 x 36 and 40 x 12. Native Developer typing screens were
confirmed fullscreen after normal cmd, PowerShell and WezTerm starts. The four
protected startup files retained their SHA-256 hashes.
