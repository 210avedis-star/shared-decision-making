# Heidi macro: rules for Claude Code

This file goes in the `heidi-session/` subfolder of **Clinic Macros**. The root `Clinic Macros/CLAUDE.md` (green zones, the five rules, export-file rules) still applies. This file adds the rules for testing the Heidi session macro.

## What this project is

`heidi_add_session.applescript` is an AppleScript macro. It reads a patient's upcoming appointment in AdvancedMD (AMD) in Google Chrome, then sets up a Heidi Health session for it. It drives the real Chrome window with real keystrokes and clicks.

## Patient-data rules (never break these)

1. **Test patient only.** Run the macro only in test mode: `osascript heidi_add_session.applescript --test <TestLastName>`. Never run it without `--test`. Never run it while a real patient's chart is open.
2. **Never look at AMD or Heidi pages yourself.** No screenshots, no reading page HTML, no `execute javascript` of your own, no browser tools on those sites. Everything you learn about a run comes from `test/reports/latest.md` and the macro log.
3. **Never open, print or copy** anything in `~/Downloads`, Chrome's profile folder, Notification Center data or clipboard history. The leak-check script searches those places and reports only PASS/FAIL, counts and file paths.
4. **Never weaken a safety feature to make a test pass.** That includes the chart patient-ID check, `redact()`, test mode, the leak checks and the forbidden-pattern lint.
5. **Never write patient data** to any file, log, commit, comment or message. The test patient's details live only in `test/config.local.sh`, which is git-ignored.
6. **The macro must never** save a PDF to disk, write to the clipboard, put a name in a notification, or keep patient values in `property` variables.

## How to work

- After every change, run `test/cycle.sh static`. It must pass before a live run.
- Live runs (`test/cycle.sh live`) take over the keyboard and mouse. Only start one when the person has said live runs are OK in this session, by typing **"live OK"**. If you're unsure, ask.
- Follow the loop in `TEST_LOOP.md`. Stop and report when it says to stop.
