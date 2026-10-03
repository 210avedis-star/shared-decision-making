# Task 3: Automated test loop for the Heidi macro

## Goal

After each change, Claude Code checks the macro by itself and gets a report saying either **PASS** or **where it broke**: which stage, which step and why. It fixes the problem and runs again, stopping when everything passes or a person is needed. All of this uses a **test patient**, and no patient data appears in anything Claude Code reads.

```
 edit ──► STATIC checks ──fail──► fix ─┐
            │ pass                     │
            ▼                          │
          LIVE run on test patient     │
            │                          │
            ▼                          │
          LEAK checks ──► REPORT ──fail┘
                            │ pass
                            ▼
                         SUMMARY → person
```

---

## 1. One-time setup (done by a person)

1. **Project folder** on the clinic Mac, for example `~/clinic-macros/heidi/`. It's a git repo containing:
   - `heidi_add_session.applescript`: the v19 macro as plain text. If Keyboard Maestro has the script pasted inline, copy it out to this file, and point Keyboard Maestro at the file ("Execute AppleScript" → "Execute script file").
   - `CLAUDE.md`, `EDITS.md`, `TEST_LOOP.md` (these files).
   - `.gitignore` with `test/config.local.sh`, `test/reports/`, `test/tmp/`.
2. **Test patients in AMD.** Use made-up demographics, not a real person:
   - **Test A (existing):** for example `TESTPATIENT, ZED Q`, DOB `01/02/1990`, email `zed.test@example.com`, with an upcoming appointment. It must already exist in Heidi.
   - **Test N (new):** for example `TESTNEW, YARA`, with an upcoming appointment. Before each new-patient test, a person deletes it from Heidi.
   - Ask the AMD admin how test patients are kept out of billing and reports.
3. **`test/config.local.sh`** (git-ignored; fake data only):
   ```sh
   TEST_LAST="Testpatient"; TEST_FIRST="Zed"; TEST_DOB="01/02/1990"; TEST_EMAIL="zed.test@example.com"
   NEW_LAST="Testnew";      NEW_FIRST="Yara"; NEW_DOB="03/04/1985"; NEW_EMAIL="yara.test@example.com"
   MACRO="$HOME/clinic-macros/heidi/heidi_add_session.applescript"
   ```
4. **Mac permissions** for the app Claude Code runs in (Terminal, iTerm or the Claude app):
   - System Settings › Privacy & Security › **Accessibility**: on (for real keystrokes and clicks).
   - **Automation**: allow it to control Google Chrome and System Events.
   - Chrome › View › Developer › **Allow JavaScript from Apple Events**: on.
   - Optional: **Full Disk Access**, so the leak check can read the Notification Center database. Without it, that check reports SKIP.
5. **Claude Code permissions.** Add these to the project's `.claude/settings.json` allow list so the loop runs without prompts: `Bash(test/cycle.sh:*)`, `Bash(osacompile:*)`, `Bash(git add:*)`, `Bash(git commit:*)`, `Bash(git diff:*)`.
6. **Before a live run:** log in to AMD and Heidi in Chrome. Open **Test A's upcoming appointment** in AMD. **Don't use the Mac during live runs.** The macro types real keystrokes into the front window.

---

## 2. Scripts Claude Code builds first (in `test/`)

| Script | What it does |
|---|---|
| `lint.sh` | Forbidden and required patterns in the macro source (§3). Prints PASS/FAIL per rule with line numbers. |
| `compile.sh` | `osacompile -o test/tmp/macro.scpt "$MACRO"`. Fails on any compile error. |
| `js_syntax.sh` | Pulls each `JS_*` property out of `test/tmp/macro.scpt` (`osascript -e 'set s to load script POSIX file "…"' -e 'JS_HEIDI of s'`) into `test/tmp/*.js`, then parses each one: `node --check` if Node is installed, otherwise JXA `new Function(src)`. |
| `redact_test.applescript` | Loads `test/tmp/macro.scpt` and calls `redactWith()` on fake strings (§4). |
| `leakcheck.sh` | Searches everywhere patient data could leak (§5). Never prints matched text. |
| `live_run.sh <case>` | Preflight → snapshot → runs the macro in test mode → collects result → leak check → writes the report (§6). |
| `cycle.sh static\|live <case>\|all` | Runs the above in order and stops at the first failing level. Always ends by writing `test/reports/latest.md`. |

Shell scripts are POSIX `sh`/`bash` for macOS. macOS has no `timeout`, so `live_run.sh` runs the macro in the background and kills it after 600 s.

---

## 3. Lint rules (`lint.sh`)

**Must NOT appear** (FAIL with line number):

| Pattern | Why |
|---|---|
| `set the clipboard` | No clipboard. |
| `path to downloads folder`, `km_chart`, `base64 -D`, `base64 -i` | No PDF on disk. |
| `emailFromPDF`, `CHART_EMAIL` | Removed. |
| `property RUNLOG` | Properties can be saved into the script file. |
| `display notification` on a line that also has `patientName`, `apptDate`, `apptTime` or `pdfName` | Lock screen. |
| `addLog(` on a line that also has `patientName`, `apptDate`, `apptTime`, `amdIds`, `pdfName` or `repId &` | Log. |
| `error "` on a line that also has `& patientName`, `& apptDate`, `(item 4 of r)` or `repId &` | Keyboard Maestro log. |
| `log(pageMap())`, `'A=' + JSON.stringify`, `JSON.stringify(appts)`, `docDiag()` in a `return` | Page text in the log. |
| `quoted form of repURL` | Patient ID in a shell argument. |
| `v: 19`, `v === 19` | Old page library would stay loaded. |

**MUST appear** (FAIL if missing):
- `global RUNLOG, PHI_WORDS, TEST_LAST`
- `on redactWith(`, `on idFromURL(`, `on emailFromDemographics(`
- `H.clear = function`, `if (window.__kmTest) throw`
- `v: 20`
- `(function(){" & testFlag`
- `RESULT: PASS`, `RESULT: FAIL`
- `STAGE amd-read`, `STAGE amd-email`, `STAGE heidi-phase1`, `STAGE amd-chart`, `STAGE heidi-phase2`

---

## 4. `redactWith` tests (fake data only)

| Input | Words | Must NOT contain afterwards | Must contain |
|---|---|---|---|
| `Testpatient, Zed Q \| 01/02/1990 \| zed.test@example.com \| 1234567` | `{"Testpatient","Zed","01/02/1990","zed.test@example.com","1234567"}` | each word | `[phi]` |
| `TESTPATIENT came in` | `{"Testpatient"}` | `TESTPATIENT` | `came in` |
| `Click Li here` | `{"Li"}` | ` Li ` | `Click` (not `C[phi]ck`) |
| `Other, Person 03/04/1985 other@x.org 98765` | `{}` | `Other, Person`, `03/04/1985`, `other@x.org`, `98765` | `[name]`, `[date]`, `[email]`, `[id]` |
| `STEP set the session date & time` | `{}` | (nothing) | the input unchanged |

(`\|` in the table means a plain `|`.)

If calling a handler of a loaded script fails because of the Foundation framework, run the test inside `osascript` with `use framework "Foundation"` at the top of the test script too.

---

## 5. Leak checks (`leakcheck.sh`)

Search terms: the test patient's last name, first name, DOB, DOB without slashes, and email, from `config.local.sh`.

Before each run, `live_run.sh` creates `test/tmp/marker` and sets the clipboard to a sentinel `km-sentinel-<timestamp>`.

| # | Check | FAIL when |
|---|---|---|
| L1 | Macro log `~/Library/Logs/Heidi macro log.txt` | It contains any term, an email, an `MM/DD/YYYY` date, or a 5+ digit number. |
| L2 | `~/Downloads` | Any file newer than the marker. |
| L3 | `$TMPDIR` and `/tmp` | Any `km_chart*` file, or any file newer than the marker that contains a term. |
| L4 | Clipboard | `pbpaste` isn't exactly the sentinel. |
| L5 | Macro source and compiled script | Either contains a term. |
| L6 | Spotlight | After waiting 20 s, `mdfind -onlyin ~ "<term>"` finds anything outside the project folder. |
| L7 | Keyboard Maestro | A term found in `~/Library/Application Support/Keyboard Maestro/` or `~/Library/Logs/Keyboard Maestro/`. |
| L8 | Notification Center database | A term found in it. SKIP if it can't be read. |
| L9 | The report itself | `test/reports/latest.md` contains a term. If so, the report is rewritten with only check names and results. |

**Output rule:** one line per check: `L1 PASS`, `L3 FAIL 2 files: <paths>`, `L8 SKIP no access`. It never prints the matched text. Paths are allowed, because only test data can match.

**Prove the leak checker works (once):** a person runs **v19** from Keyboard Maestro on Test A, then Claude Code runs `test/leakcheck.sh` alone. It must FAIL at least L1 and L4. If it passes, the checker is broken; fix it before trusting any v20 result.

---

## 6. Live run and report (`live_run.sh <case>`)

**Cases**

| Case | Who starts it | Setup | Command | Expected |
|---|---|---|---|---|
| `A` existing | Claude, repeatable | Test A's appointment open | `osascript "$MACRO" --test "$TEST_LAST"` | Exit 0. Log has `RESULT: PASS` and `Outcome: existing patient`. All leak checks pass. |
| `G` guard | Claude, repeatable | Test A open | `osascript "$MACRO" --test "Wrongname"` | Exit ≠ 0. Log has `TEST MODE: the patient on screen is not the test patient`. No `STAGE heidi-phase1` in the log. All leak checks pass. |
| `N` new | Person first | Test N deleted from Heidi, Test N's appointment open | `… --test "$NEW_LAST"` (leak terms switch to `NEW_*`) | Exit 0. `Outcome: new patient`. `Chart report matches the patient on screen: true`. `PDF received:` in the log. All leak checks pass. |
| `K` Keyboard Maestro | Person | Test A open | Run the macro from Keyboard Maestro (normal mode) | Works as before. Then Claude runs `leakcheck.sh` alone, and all checks pass. |

**Preflight.** Stop with a clear `ENVIRONMENT` result if any of these fail:
- Chrome is running.
- A tab with `advancedmd.com` and one with `heidihealth.com` exist. Print yes/no only, never the URLs.
- `execute javascript "1+1"` in the Heidi tab returns 2.
- System Events responds.

**`test/reports/latest.md` format.** It's built only from the redacted log and the script results.

```markdown
# Heidi macro test — case A — 2026-10-03 14:05 — RESULT: FAIL
Exit code: 1 · Duration: 74 s · Macro version: 20 · Git commit: abc1234

## Where it broke
Stage: heidi-phase1
Step: set the session date & time
Reason: x date did not stick
Needed a person: no

## Last 40 log lines
(redacted log lines)

## Leak checks
L1 PASS · L2 PASS · L3 PASS · L4 PASS · L5 PASS · L6 PASS · L7 PASS · L8 SKIP

## Where to look
heidi-phase1 / "set the session date & time" → JS_HEIDI: setDateTime(), openEditor(), typeTime(), pickDay()
```

**How the report finds the break.** The stage is the last `STAGE` line. The step is the last `STEP` line. The reason is the first `x …` or `FAILED` line after it, or the `RESULT: FAIL` text.

**"Where to look" map**

| Stage | Code |
|---|---|
| `amd-read` | `JS_AMD_READ`, top of `mainFlow` |
| `amd-email` | `emailFromDemographics`, `JS_AMD_EMAIL` |
| `heidi-phase1` | `H.phase1`. The step name points to the block: "start a new Heidi session", "find or create the patient", "add the … template", "fill in the new patient details", "set the session date & time". |
| `amd-chart` | `getChartPDF`, `JS_AMD_PRINT`, `JS_REPORT_PDF` |
| `heidi-phase2` | `H.phase2` (attach, then context) |
| none / `ENVIRONMENT` | Preflight: logins, tabs, permissions |

Keep timestamped copies as `test/reports/run-<time>-<case>.md`. They're git-ignored.

---

## 7. The loop Claude Code follows

1. **Static first:** `test/cycle.sh static`. Fix and re-run until it passes.
2. **Live only with permission:** run live cases only after the person has typed **"live OK"** in this session. Start with `G`, then `A`.
3. **Read `test/reports/latest.md`** and classify the result:

   | Kind | Action |
   |---|---|
   | **Leak** (any L-check FAIL) | Highest priority. Fix it in the macro. Never change the check. |
   | **Bug from the v20 edits** | Compare with v19 (`git diff v19 -- heidi_add_session.applescript`). Make the smallest fix. |
   | **"needs a person"** at a step v19 did automatically | Treat it as a bug from the edits (above). |
   | **ENVIRONMENT** (logged out, missing tab, permission, popup blocked) | Stop and tell the person exactly what to fix. |
   | **Heidi or AMD page changed** (an element not found that v19 also can't find) | Stop. Report the step and a proposed fix. Don't guess at page structure. |

4. **One fix per cycle.** Commit it as `v20 fix: <stage>/<step>: <what changed>`. No patient data in commit messages.
5. Repeat from step 1.
6. **Stop** and write `test/reports/SUMMARY.md` when any of these happens:
   - all repeatable cases (`G`, `A`) pass with every leak check passing;
   - 5 live runs have been used in this session;
   - the same stage and step fails twice in a row after a fix;
   - an ENVIRONMENT or page-changed result;
   - a fix would need reading page content or weakening a safety feature.
7. **SUMMARY.md** lists: each case and its result; the fixes made (commit hashes); open problems with stage, step and reason; what the person still has to do (cases `N` and `K`, and a visual check that Notification Center has no names).

---

## 8. Feature versions

`FEATURES.md` adds cases for v21–v23 (`P`, `D`, `T`, and new expectations for `A` and `N`). Add each version's cases to `live_run.sh` and the stop condition before starting that version. From v23 on, the report also shows `Duration` against the previous version.

---

## 9. One-command use

Save this as `.claude/commands/verify-macro.md` in the project. The person can then type `/verify-macro` in Claude Code:

```markdown
Run the Heidi macro test loop in TEST_LOOP.md §7.
Follow CLAUDE.md rules. Static checks first. Live cases only if I have said "live OK" in this session.
Fix one problem per cycle and commit it. Stop on the stop conditions and give me SUMMARY.md in a few lines:
what passed, what broke (stage / step / reason), what you changed, what I need to do.
```
