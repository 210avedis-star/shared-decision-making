# Heidi macro: hand-off pack for Claude Code

| File | For | What it is |
|---|---|---|
| `CLAUDE.md` | Claude Code | Patient-data rules it must follow in the macro project. |
| `EDITS.md` | Claude Code | Task 1: goals and exact edits for v20 (HIPAA fixes, test mode, stage markers). Task 2: small SDM form edits. |
| `TEST_LOOP.md` | You + Claude Code | Task 3: one-time setup, the test scripts to build, leak checks, report format, and the fix-and-retest loop. |

## How to use it

1. Do the one-time setup in `TEST_LOOP.md` §1: project folder, test patients, `config.local.sh`, Mac permissions.
2. Copy these three files into the project folder, next to `heidi_add_session.applescript`.
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
