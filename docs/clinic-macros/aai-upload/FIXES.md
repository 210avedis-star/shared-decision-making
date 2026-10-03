# aai-upload ("W AAI Doc to PDF, Gmail, AdvancedMD upload", ⌘2): fixes

## What it does

1. Reads the AAI Google Doc's text.
2. Has Chrome download the Doc as a PDF into Downloads.
3. Builds the email.
4. **Moves the PDF into `~/AAI`** (the approved exception; the PDF stays there).
5. Makes a Gmail draft with the PDF attached.
6. Fills in the AdvancedMD "New Upload" form for the patient's chart, and clicks **Upload to Chart** if all checks pass. It never signs.

It already follows most rules: no clipboard, no log file, generic notifications. `rail.txt` holds only a screen position.

## Goals

1. **Never delete, move or rename anything in `~/AAI`.** Moving the new PDF *into* `~/AAI` stays as it is.
2. **Nothing left in Downloads**, even when the macro stops partway.
3. The macro follows the contract in `TESTING.md` §3 (test mode, log, `STAGE` markers).
4. **Everything else works exactly as now.**

## Edits

1. **Standard block.** Add the standard block from `_template/macro.applescript` (C4) with `LOG_NAME` = `aai-upload`. The current `on run` body becomes `mainFlow()`. Keep its own `try … on error` dialog behavior.
2. **`STAGE` markers.** Use the existing `stepName` points: `doc-read` (step 2), `email-build` (3), `pdf-save` (4), `gmail` (5), `amd-open` (6–7), `amd-form`, `amd-upload`.
3. **Patient values into `PHI_WORDS`:** right after `fl` is split, add `patientEmail`, `fileBase` and the name parts of `fileBase`.
4. **Test-mode guard:** right after the note is parsed, and **before the PDF is moved to `~/AAI`**, call `checkTestPatient(<last name from the note>)`.
5. **Nothing left in Downloads.** If the macro stops **before step 4** for any reason, delete the PDF it just downloaded (`dlPath`) from Downloads before stopping. That covers the stops in steps 2 and 3, the visit-time dialog and test-mode failures. *Why delete and not move:* before step 4 the macro doesn't yet know the file name, and the Google Doc still holds the original, so nothing is lost. **Ask the person to confirm this behavior before building it** (the root `CLAUDE.md` says to ask before any change that deletes something).
6. **Dialogs become `needsPerson(...)` in test mode:**
   - "The visit time isn't on the DOV line" → `needs a person at email-build`;
   - "Couldn't open the chart automatically …" → `needs a person at amd-open`;
   - the "click the documents/upload icon once" learning step → `needs a person at amd-open`.
7. **Test mode never clicks Upload to Chart.** It fills the form, runs all checks, logs `form ready`, and stops. That keeps test documents out of the test chart; case `U` (person) covers a real upload.
8. **Log lines** mirror the existing `notes` list. Those are already generic, for example `PDF saved` or `email drafted with PDF attached`. Pass them through `addLog`.
9. **`lint.extra`:**
   ```
   allow moveItemAtPath:dlPath toPath:pdfPath   # moving the new PDF INTO ~/AAI is approved
   forbid removeItemAtPath:pdfPath               # never delete in ~/AAI
   require autoUpload and TEST_LAST is ""        # test mode never clicks Upload to Chart
   ```

## `test.conf`

```sh
MACRO_ID="aai-upload"; TITLE="AAI Doc to PDF, Gmail, AdvancedMD upload"; HOTKEY="⌘2"; SCRIPT="macro.applescript"
LOG="$HOME/Library/Logs/Clinic Macros/aai-upload.log"
NEEDS_TABS="docs.google.com advancedmd.com"
SETUP="Open Test A's fake AAI Google Doc in Chrome. Have AdvancedMD open and logged in."
ALLOWED_PATHS="$HOME/AAI"; CLIPBOARD="untouched"; TERMS="TEST"; JS_PROPS="^js"
AUTO_CASES="G A"; PERSON_CASES="U"
case_G() { RUN --test "Wrongname"; EXPECT_FAIL "TEST MODE: the patient on screen is not the test patient"; EXPECT_NO "STAGE pdf-save"; }
case_A() { RUN --test "$TEST_LAST"; EXPECT_PASS; EXPECT "STAGE amd-form"; EXPECT "form ready"; }
case_U() { ASK_PERSON "Run ⌘2 normally on Test A's AAI Doc (it will upload to the test chart), then say done."; LEAKCHECK_ONLY; }
```

Each case `A` run adds a test PDF to `~/AAI` (L10 reports it) and a Gmail draft. The person deletes those now and then; Claude Code never touches `~/AAI`.

## Stage → code map (for reports)

| Stage | Code |
|---|---|
| `doc-read` | step 2: the mobilebasic fetch, PDF export, `waitDownload`, the .txt and PDF fallbacks |
| `email-build` | `jsParse` / `__aaiBuild` |
| `pdf-save` | step 4: the move into `~/AAI` |
| `gmail` | step 5 |
| `amd-open` | chart opening, `upJS`, `rail.txt`, `realClick` |
| `amd-form` / `amd-upload` | `selJS`, `fillJS`, `checkJS`, Upload to Chart |
