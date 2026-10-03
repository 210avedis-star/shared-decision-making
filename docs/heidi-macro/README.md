# Heidi macro: hand-off pack for Claude Code

| File | For | What it is |
|---|---|---|
| `CLAUDE.md` | Claude Code | Patient-data rules it must follow in the macro project. |
| `EDITS.md` | Claude Code | Task 1: goals and exact edits for v20 (HIPAA fixes, test mode, stage markers). Task 2: small SDM form edits. |
| `TEST_LOOP.md` | You + Claude Code | Task 3: one-time setup, the test scripts to build, leak checks, report format, and the fix-and-retest loop. |
| `FEATURES.md` | Claude Code | Task 4: your requested changes. **v21** demographics for every patient, chart for every patient, correct note template, Dr. Hey vs PA. **v22** chart since last visit, 200-page cap. **v23** faster. **Later:** the morning run. |

## Order of work

1. **v20:** HIPAA fixes + test mode (`EDITS.md`), proven with the test loop (`TEST_LOOP.md`).
2. **v21–v23:** your feature changes (`FEATURES.md`). Each one is checked with the same loop.
3. **Later:** the unattended morning run, after you approve Playwright.

The HIPAA fixes and test loop come first because every later change is tested with them.

## How to use it

1. Do the one-time setup in `TEST_LOOP.md` §1: project folder, test patients, `config.local.sh`, Mac permissions.
2. Copy these four files into the project folder, next to `heidi_add_session.applescript`.
3. Open Claude Code in that folder and paste the prompts below, one at a time.

### Prompt 1: make the edits

```
Read CLAUDE.md and EDITS.md. First commit heidi_add_session.applescript as-is and tag it v19.
Then do Task 1 exactly as written, in order. If any "find" text isn't found exactly, stop and tell me which one.
Don't change anything EDITS.md doesn't list. Commit as "v20: HIPAA fixes, test mode, stage markers".
```

### Prompt 2: build the test tools

```
Read TEST_LOOP.md. Build the scripts in §2 to the rules in §3–§6, plus .gitignore and
.claude/commands/verify-macro.md from §8. Run "test/cycle.sh static" and fix the macro until it passes.
Don't do any live runs yet. Show me the static results.
```

### Prompt 3: prove the leak checker works

First run the **old v19** once yourself from Keyboard Maestro on Test A. Then:

```
Run test/leakcheck.sh against the run I just did with v19 (Test A terms). It must FAIL at least L1 and L4.
If it passes, the checker is broken: fix it and tell me what was wrong.
```

### Prompt 4: run the loop

Open Test A's upcoming appointment in AMD, make sure AMD and Heidi are logged in, then step away from the Mac:

```
live OK
/verify-macro
```

When it stops, it gives you the summary: what passed, where it broke (stage / step / reason), what it changed, and what you need to do. Then do cases `N` (new patient) and `K` (Keyboard Maestro run) with it, as listed in `TEST_LOOP.md` §6.

### Prompt 5: diagnostics for the feature work

Open Test A's upcoming appointment (one with **Dr. Hey**) and its Heidi session, then:

```
live OK
Read FEATURES.md §1. Add the --diag mode and run D1, D2, D3 and D4 on the test patient.
Run the leak check on each diag file. Show me the four diag reports and stop.
```

Then tell Claude Code:
- which note type names from D3 count as a Hey/PA clinic note, an AAI note or an Op note;
- whether Chart Print shows the newest pages first or last;
- whether AMD values may overwrite different Heidi demographics (recommended: yes).

### Prompt 6: v21, v22, v23

```
live OK
Do FEATURES.md v21. Add its test cases to the loop, then run /verify-macro until it passes or stops.
Then the same for v22, then v23. Stop after each version and give me the summary before starting the next.
```

For case `P` (PA appointment) and case `N` (new patient), it will ask you to open a different appointment or delete the test patient from Heidi first.
