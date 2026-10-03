# Clinic Macros: shared test system

**One test system for every macro in this folder, now and in the future.** After any change, Claude Code checks the macro by itself, using a **fake patient**. It gets a report that says either **PASS** or **where it broke** (stage, step, reason), fixes the problem and runs again. It stops when everything passes or a person is needed. Nothing Claude Code reads contains real patient data.

```
 change ──► STATIC checks ──fail──► fix ─┐
              │ pass                     │
              ▼                          │
            LIVE run on fake patient     │
              │                          │
              ▼                          │
            LEAK checks ──► REPORT ──fail┘
                              │ pass
                              ▼
                           SUMMARY → person
```

---

## 1. Rules for Claude Code when testing (every macro)

1. **Fake patients only.** Live runs happen only in test mode (`--test <TestLast>`). Never run a macro without `--test`. Never run one while a real patient's record is open.
2. **Never look at clinical pages yourself:** AdvancedMD, Heidi, Gmail, Google Docs or Weave. No screenshots, no reading page HTML, no `execute javascript` of your own, no browser tools on those sites. Everything you learn about a run comes from the macro's PHI-free log and the report.
3. **Never open, print or copy** anything in `~/Downloads`, `~/AAI`, Chrome's profile, Notification Center data or clipboard history. The leak check looks there and reports only PASS/FAIL, counts and file paths.
4. **Never delete, move or rename anything in `~/AAI`.** Test PDFs that land there are removed by a person.
5. **Never weaken a safety feature to make a test pass.** That covers patient-match checks, `redact()`, test mode, leak checks and lint rules.
6. **Live runs take over the keyboard and mouse.** Only start one after the person has typed **"live OK"** in this session. If unsure, ask.
7. **Fake data lives only in `testkit/config.local.sh`** (git-ignored). Never put it in reports, commits or messages.

---

## 2. Folder layout

```
Clinic Macros/
  CLAUDE.md                       project rules (yours)
  START_HERE.md  TESTING.md       this system
  Clinic Macros Macros.kmmacros   original export (never changed)
  macros-fixed-vN.kmmacros        new exports Claude Code makes
  testkit/                        shared test tools (Claude Code builds, §5)
    config.local.sh               fake patients (git-ignored)
    reports/<macro-id>/           reports (git-ignored)
  _template/                      starting point for new macros (§9)
    macro.applescript  test.conf
  heidi-session/                  one folder per macro
    macro.applescript  test.conf  lint.extra  EDITS.md  FEATURES.md
  heidi-to-doc/
    macro.applescript  test.conf  lint.extra  FIXES.md
  aai-upload/
    macro.applescript  test.conf  lint.extra  FIXES.md
```

Keyboard Maestro runs each macro's `macro.applescript` file ("Execute AppleScript" → "Execute script file"). So a fix Claude Code makes reaches Keyboard Maestro without a new import.

---

## 3. The macro contract

**Every macro must follow these rules**, the three existing ones and every future one. `testkit/lint.sh` checks them.

| # | Rule | How it's checked |
|---|---|---|
| C1 | **Lives in its own folder** as `macro.applescript`, with a `test.conf`. Keyboard Maestro runs the file. | Folder scan |
| C2 | **Test mode.** `on run argv` accepts `--test <TestLast>`. In test mode the macro:<ul><li>stops **before doing anything** if the patient on screen isn't the test patient (`TEST MODE: the patient on screen is not the test patient. Nothing was changed.`);</li><li>never waits for a person. Any dialog, banner or "click Continue" becomes an immediate failure: `needs a person at <step>`.</li></ul> | Lint + case `G` |
| C3 | **The log has no patient data.** Lines go to `~/Library/Logs/Clinic Macros/<macro-id>.log` (last run only; `heidi-session` may keep its existing log path, set in `test.conf`). Every line passes through `redact()`. The log contains `STAGE <name>` at each major stage, and ends with `RESULT: PASS` or `RESULT: FAIL — <generic reason>`. | Lint + L1 |
| C4 | **The standard block** (from `_template/macro.applescript`): `global RUNLOG, PHI_WORDS, TEST_LAST`, the `on run argv` handler, `addLog`, `saveLog`, `redact`, `redactWith`, and `PHI_WORDS` filled with the patient's details as soon as they're read. | Lint |
| C5 | **No patient data outside the green zones:**<ul><li>no files, except paths listed in `ALLOWED_PATHS` (only `~/AAI`, for `aai-upload`);</li><li>nothing left in Downloads or temp folders;</li><li>clipboard cleared after use;</li><li>generic notifications and error messages;</li><li>no `property` holding patient values.</li></ul> | Lint + L2–L8 |
| C6 | **Never deletes, moves or renames** anything in `~/AAI`. | Lint |

### Common lint rules (`testkit/lint.sh`, all macros)

**Must not appear** (FAIL with line number):

| Pattern | Why |
|---|---|
| `set the clipboard to RUNLOG`, or `set the clipboard to` a report or diagnostic | Clipboard |
| `display notification` on a line containing a patient variable (`patientName`, `docName`, `fileBase`, `apptDate`, `apptTime`, `patientEmail`, `pdfName`) | Lock screen |
| `addLog(` on a line containing a patient variable | Log |
| `error "` or `display dialog` text built with a patient variable, in test-mode paths | Keyboard Maestro log |
| `property RUNLOG`, or any `property` set from patient data | Script file |
| `do shell script` whose argument includes a patient variable | Process list |
| `rm `, `removeItemAtPath`, `moveItemAtPath` or `trash` on a path containing `AAI` (except `aai-upload`'s **move into** `~/AAI`, which `lint.extra` allows) | C6 |

**Must appear:** `global RUNLOG, PHI_WORDS, TEST_LAST`, `on run argv`, `on redactWith(`, `RESULT: PASS`, `RESULT: FAIL`, `TEST MODE: the patient on screen is not the test patient`, and at least one `STAGE `.

**Per-macro extras** go in `<macro>/lint.extra`, one rule per line:
```
forbid <regex>   # reason
require <regex>  # reason
allow <regex>    # exception to a common rule, with reason
```

---

## 4. `test.conf` (one per macro)

This is a shell file that describes how to test the macro. Example:

```sh
MACRO_ID="heidi-session"
TITLE="Heidi – Add Upcoming Session"
HOTKEY="⌘3"
SCRIPT="macro.applescript"
LOG="$HOME/Library/Logs/Heidi macro log.txt"
NEEDS_TABS="advancedmd.com heidihealth.com"        # preflight: these tabs must exist
SETUP="Open Test A's upcoming appointment in AdvancedMD. Log in to Heidi."
ALLOWED_PATHS=""                                   # e.g. "$HOME/AAI"
CLIPBOARD="untouched"                              # untouched | cleared
TERMS="TEST"                                       # which fake patient: TEST or NEW (from config.local.sh)
AUTO_CASES="G A"                                   # Claude may run these over and over
PERSON_CASES="N K"                                 # need a person first
JS_PROPS="^JS_"                                    # text properties holding JavaScript (parsed by js_syntax.sh)

case_G() { RUN --test "Wrongname"; EXPECT_FAIL "TEST MODE: the patient on screen is not the test patient"; EXPECT_NO "STAGE heidi-phase1"; }
case_A() { RUN --test "$TEST_LAST"; EXPECT_PASS; EXPECT "Outcome: existing patient"; }
case_N() { TERMS=NEW; ASK_PERSON "Delete Test N from Heidi and open Test N's appointment."; RUN --test "$NEW_LAST"; EXPECT_PASS; EXPECT "Outcome: new patient"; }
case_K() { ASK_PERSON "Run the macro from Keyboard Maestro (normal mode), then say done."; LEAKCHECK_ONLY; }
```

`testkit/lib.sh` provides `RUN`, `EXPECT`, `EXPECT_NO`, `EXPECT_PASS`, `EXPECT_FAIL`, `ASK_PERSON` (it stops the loop and tells the person what to do) and `LEAKCHECK_ONLY`.

---

## 5. `testkit/` (Claude Code builds these once; they work for every macro)

| Script | What it does |
|---|---|
| `cycle.sh <macro-id\|all> static\|live [case]` | Runs the levels in order and stops at the first that fails. Always writes `reports/<macro-id>/latest.md`. With `all`, runs every macro folder that has a `test.conf`. |
| `lint.sh <macro-id>` | Common rules (§3) plus `lint.extra`. |
| `compile.sh <macro-id>` | `osacompile` into `testkit/tmp/<macro-id>.scpt`. Fails on any compile error. |
| `js_syntax.sh <macro-id>` | For every text property matching `JS_PROPS`, extracts it from the compiled script (`load script` → property) and parses it: `node --check` if Node is installed, otherwise JXA `new Function(src)`. Fragments (helper-function lists) are wrapped in `(function(){ … })` before parsing. |
| `redact_test.sh <macro-id>` | Runs the `redactWith` cases in §6 against that macro's compiled script. |
| `leakcheck.sh <macro-id>` | §7. |
| `live_run.sh <macro-id> <case>` | Preflight → snapshot → runs the case from `test.conf` (macOS has no `timeout`, so it runs the macro in the background and kills it after 600 s) → collects the log → leak check → report. |
| `new_macro.sh <macro-id>` | Copies `_template/` into a new folder (§9). |
| `lib.sh` | Helpers used by `test.conf`. |

**Preflight.** Stop with an `ENVIRONMENT` result if any of these fail:
- Chrome is running.
- Each tab in `NEEDS_TABS` exists. Print yes/no only, never the URLs.
- `execute javascript "1+1"` returns 2.
- System Events responds.

---

## 6. `redactWith` tests (fake data; same for every macro)

| Input | Words | Must NOT contain afterwards | Must contain |
|---|---|---|---|
| `Testpatient, Zed Q \| 01/02/1990 \| zed.test@example.com \| 1234567` | `{"Testpatient","Zed","01/02/1990","zed.test@example.com","1234567"}` | each word | `[phi]` |
| `TESTPATIENT came in` | `{"Testpatient"}` | `TESTPATIENT` | `came in` |
| `Click Li here` | `{"Li"}` | ` Li ` | `Click` (not `C[phi]ck`) |
| `Other, Person 03/04/1985 other@x.org 98765` | `{}` | `Other, Person`, `03/04/1985`, `other@x.org`, `98765` | `[name]`, `[date]`, `[email]`, `[id]` |
| `STAGE doc-read` | `{}` | (nothing) | the input unchanged |

(`\|` in the table means a plain `|`.)

---

## 7. Leak checks (`leakcheck.sh`, every live run)

Search terms are the fake patient's last name, first name, DOB, DOB without slashes, and email (from `config.local.sh`, chosen by `TERMS`). Before each run, `live_run.sh` creates `testkit/tmp/marker` and sets the clipboard to a sentinel, `km-sentinel-<time>`.

| # | Check | FAIL when |
|---|---|---|
| L1 | The macro's `LOG` | It contains a term, an email, an `MM/DD/YYYY` date or a 5+ digit number. |
| L2 | `~/Downloads` | Any file newer than the marker is left. |
| L3 | `$TMPDIR` and `/tmp` | A file newer than the marker contains a term. |
| L4 | Clipboard | `CLIPBOARD=untouched`: it isn't exactly the sentinel. `CLIPBOARD=cleared`: it contains a term. |
| L5 | `macro.applescript` and the compiled script | Either contains a term. |
| L6 | Spotlight | After waiting 20 s, `mdfind -onlyin ~ "<term>"` finds anything outside `Clinic Macros/` and `ALLOWED_PATHS`. |
| L7 | Keyboard Maestro | A term found in `~/Library/Application Support/Keyboard Maestro/` or `~/Library/Logs/Keyboard Maestro/`. |
| L8 | Notification Center database | A term found in it. SKIP if it can't be read (needs Full Disk Access). |
| L9 | The report | `latest.md` contains a term. If so, it's rewritten with check names and results only. |
| L10 | `ALLOWED_PATHS` | Never fails. Reports how many new files appeared, for the person to tidy. Never deletes. |

**Output rule:** one line per check (`L1 PASS`, `L2 FAIL 1 file: <path>`, `L8 SKIP no access`). Never print matched text.

**Prove the checker works** (once per macro, before trusting it): a person runs the **original** macro from the original export on the fake patient, then Claude runs `leakcheck.sh <macro-id>` alone. It must FAIL where the original is known to leak:

| Macro | Must fail |
|---|---|
| `heidi-session` | L1, L4 |
| `heidi-to-doc` | L4 |
| `aai-upload` | L2, but only if the person stops the macro partway |

---

## 8. Report and the loop

**`testkit/reports/<macro-id>/latest.md`** (timestamped copies are kept too):

```markdown
# heidi-session — case A — 2026-10-03 14:05 — RESULT: FAIL
Exit code: 1 · Duration: 74 s · Git commit: abc1234
## Where it broke
Stage: heidi-phase1 · Step: set the session date & time · Reason: x date did not stick · Needed a person: no
## Last 40 log lines
(redacted)
## Leak checks
L1 PASS · L2 PASS · L3 PASS · L4 PASS · L5 PASS · L6 PASS · L7 PASS · L8 SKIP · L10 0 new
```

**How the report finds the break.** Stage is the last `STAGE` line. Step is the last `STEP` line. Reason is the first `x …` or `FAILED` line after it, or the `RESULT: FAIL` text. Each macro's FIXES, EDITS or FEATURES file maps stages to code.

**The loop** (`/verify-macro <macro-id|all>`):
1. `testkit/cycle.sh <id> static`. Fix and repeat until it passes.
2. Only after "live OK": run the `AUTO_CASES`, guard case `G` first.
3. Read `latest.md` and classify:

   | Kind | Action |
   |---|---|
   | **Leak** | Highest priority. Fix the macro. Never change the check. |
   | **Bug from our edits** | Compare with the original (`git diff <macro-id>-original`). Smallest fix. |
   | **"needs a person"** at a step the original did by itself | Treat as a bug from our edits. |
   | **ENVIRONMENT** (logged out, missing tab, permission) | Stop. Tell the person exactly what to fix. |
   | **Page changed** (an element the original can't find either) | Stop. Report the step and a proposed fix. |

4. One fix per cycle. Commit it as `<macro-id> fix: <stage>/<step>: <what>`.
5. **Stop** and write `reports/<macro-id>/SUMMARY.md` when any of these happens:
   - all `AUTO_CASES` pass with clean leak checks;
   - 5 live runs on this macro in this session;
   - the same stage and step fails twice after a fix;
   - an ENVIRONMENT or page-changed result;
   - a fix would need reading page content or weakening a safety feature.
6. **SUMMARY.md** lists: each case and its result, the commits, open problems (stage / step / reason), and what the person must still do (`PERSON_CASES`, tidying `ALLOWED_PATHS`, a visual check of Notification Center).

**`.claude/commands/verify-macro.md`** (Claude Code fills in `$ARGUMENTS` with what you type after the command):
```markdown
Run the shared test loop in TESTING.md §8 for: $ARGUMENTS (a macro folder name, or "all").
Follow CLAUDE.md and TESTING.md §1. Static checks first. Live cases only if I have said "live OK" in this session.
One fix per cycle, committed. Stop on the stop conditions and give me SUMMARY.md in a few lines per macro:
what passed, what broke (stage / step / reason), what you changed, what I need to do.
```

---

## 9. Adding a new macro (every future macro)

1. `testkit/new_macro.sh <macro-id>` copies `_template/`. The template already has the standard block, test mode, `STAGE` markers and a `test.conf` with cases `G` and `A`.
2. Build the macro with fake data only. Add a `STAGE` line at each major step. Read the patient's details into `PHI_WORDS` as early as possible.
3. Fill in `test.conf`: setup, tabs, `ALLOWED_PATHS` (normally empty), `CLIPBOARD`, cases.
4. `/verify-macro <macro-id>` until it passes.
5. Write the **data-flow check** (`<macro-id>/DATAFLOW.md`, plain language): what it reads, moves, stores and leaves behind. Anything outside the green zones must already be fixed, or be an approved exception in `CLAUDE.md`.
6. Add it to a new export file, `macros-fixed-vN.kmmacros`.

**A macro is ready for real patients only when** static passes, all `AUTO_CASES` pass with clean leak checks, `PERSON_CASES` are done, and `DATAFLOW.md` is written.

**`_template/macro.applescript`** must contain:
- the standard block from `heidi-session` v20: `global RUNLOG, PHI_WORDS, TEST_LAST`, `on run argv` with the `--test` parsing, `addLog`, `saveLog` (path from a `LOG_NAME` property), `redact`, `redactWith`;
- a `needsPerson(stepName)` handler: in test mode it raises `needs a person at <step>`, otherwise it shows the dialog;
- a `checkTestPatient(lastName)` handler that raises the C2 guard error;
- a `notify(msg)` handler that only shows generic text;
- an empty `mainFlow()` with example `STAGE` lines.

---

## 10. One-time setup (person)

1. **Fake patients.** Made-up names and details, never a real person:
   - **Test A:** for example `TESTPATIENT, ZED Q`, DOB `01/02/1990`, email `zed.test@example.com`.
     - In AdvancedMD: an upcoming appointment with Dr. Hey and a second one with the PA.
     - In Heidi: already a patient, with one session that has a short fake note.
     - In Google Docs: one fake AAI note for Test A.
   - **Test N:** for example `TESTNEW, YARA`, with an upcoming appointment, not in Heidi.
   - Ask the AdvancedMD admin how to keep test patients out of billing and reports.
2. **`testkit/config.local.sh`:**
   ```sh
   TEST_LAST="Testpatient"; TEST_FIRST="Zed"; TEST_DOB="01/02/1990"; TEST_EMAIL="zed.test@example.com"
   NEW_LAST="Testnew";      NEW_FIRST="Yara"; NEW_DOB="03/04/1985"; NEW_EMAIL="yara.test@example.com"
   ```
3. **Mac permissions** for the app Claude Code runs in:
   - **Accessibility:** on.
   - **Automation:** Google Chrome and System Events.
   - Chrome › View › Developer › **Allow JavaScript from Apple Events**.
   - Optional: **Full Disk Access**, for check L8.
4. **Claude Code permissions.** In `.claude/settings.json`, allow `Bash(testkit/*:*)`, `Bash(osacompile:*)`, `Bash(git add:*)`, `Bash(git commit:*)`, `Bash(git diff:*)`, `Bash(git tag:*)`.
5. **During live runs, don't use the Mac.** The macros type real keystrokes into the front window.
