# heidi-to-doc ("W HEIDI to Google Doc", ⌘1): fixes

## What it does

1. Reads the patient name at the top of the Heidi session.
2. Opens the "…" menu → **Copy all text** (the whole note goes to the clipboard).
3. Copies the Google Doc template as "<Last,First> Clinic Note".
4. Pastes the note into it.

The Google Doc is in Google Workspace, a green zone.

## Goals

1. The clinical note is on the clipboard only for the few seconds it takes to paste, then it's cleared. Heidi only offers "Copy all text", so the clipboard can't be avoided. That makes it allowed under rule 2, provided it's cleared in the same run.
2. No patient data in notifications, dialogs created for errors, the log, or shell commands.
3. The macro follows the contract in `TESTING.md` §3 (test mode, log, `STAGE` markers).
4. **Everything else works exactly as now.**

## Edits

1. **Standard block.** Add the standard block from `_template/macro.applescript` (C4) with `LOG_NAME` = `heidi-to-doc`. Wrap the current top-level code in `mainFlow()`. `on run argv` calls it.
2. **`STAGE` markers:** `heidi-read` (finding the tab and reading the name), `heidi-copy` (menu → Copy all text), `doc-copy` (Make a copy and rename), `doc-paste`.
3. **Patient values into `PHI_WORDS`:** right after the name is read, add the last and first name. Right after the copy, add the `nameParts` items.
4. **Test-mode guard:** after the name is read, call `checkTestPatient(lastName)` before opening any menu.
5. **Dialogs become `needsPerson(...)`.** Both "Type the patient name" dialogs fail in test mode with `needs a person at heidi-read`, and keep their normal behavior otherwise.
6. **Clear the clipboard after pasting.** After the final `keystroke "v" using command down`, add `delay 1` and then `set the clipboard to ""`. Also clear it in the error handler, so a failed run doesn't leave the note there.
7. **Failure diagnostics.** Remove `set the clipboard to report`. Instead:
   - log `addLog("menu item not found after " & n & " tries")`;
   - only when a `DEBUG` property is true, log the structure-only part of `diagnose()` (tags, roles, positions). Remove the `NAME:` line and all `innerText` from `diagnose()` and `menuTexts()`;
   - dialog text: `Couldn't find the "Copy all text" menu item. Details are in the Clinic Macros log.`
8. **Generic notification:** change `display notification docName & " created and note pasted."` to `notify("Clinic note created")`.
9. **`trimText` without the shell.** Replace the `do shell script "printf %s …"` version with pure AppleScript: replace returns and linefeeds with spaces, then trim leading and trailing spaces.
10. **Fake name in a comment.** The comment in the safety-check section (`-- must appear together, e.g. "…"`) contains what looks like a real patient's name. Replace it with `"Jane Doe" or "Doe, Jane"`.
11. **`lint.extra`:**
    ```
    require set the clipboard to ""   # clipboard must be cleared after paste
    forbid set the clipboard to report   # diagnostics never go to the clipboard
    ```

## `test.conf`

```sh
MACRO_ID="heidi-to-doc"; TITLE="Heidi note to Google Doc"; HOTKEY="⌘1"; SCRIPT="macro.applescript"
LOG="$HOME/Library/Logs/Clinic Macros/heidi-to-doc.log"
NEEDS_TABS="heidihealth.com"
SETUP="Open Test A's Heidi session that has the fake note. Log in to Google Docs."
ALLOWED_PATHS=""; CLIPBOARD="cleared"; TERMS="TEST"; JS_PROPS="^jsHelpers$"
AUTO_CASES="G A"; PERSON_CASES=""
case_G() { RUN --test "Wrongname"; EXPECT_FAIL "TEST MODE: the patient on screen is not the test patient"; EXPECT_NO "STAGE heidi-copy"; }
case_A() { RUN --test "$TEST_LAST"; EXPECT_PASS; EXPECT "STAGE doc-paste"; }
```

Each run of case `A` makes a new "Testpatient,Zed Clinic Note" in Google Drive. The person deletes those test docs now and then; Claude Code never does.

## Stage → code map (for reports)

| Stage | Code |
|---|---|
| `heidi-read` | `focusTab`, `readPatientName` |
| `heidi-copy` | `clickMenuButton`, `clickText`, `cands()` in `jsHelpers` |
| `doc-copy` | the "Make a copy" wait, name box, rename loop |
| `doc-paste` | the final keystrokes and clipboard clear |
