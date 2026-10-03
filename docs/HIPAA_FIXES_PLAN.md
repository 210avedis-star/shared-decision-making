# HIPAA Fixes: Edit Plan

This plan covers the edits from the data-handling review of the **Heidi – Add Upcoming Session** macro (v19, the AppleScript) and the **SDM form** (`app/`). The goal: patient data exists only in AdvancedMD (AMD), in Heidi, and briefly in memory while the macro runs. Nothing goes in files, logs, the clipboard, notifications or the script file.

Code locations for the macro use the handler or function names, because the macro isn't in this repo.

---

## Part A: Heidi macro

### A1. The chart PDF never touches the disk

| Where | Edit |
|---|---|
| `getChartPDF`: the `if b64 is not ""` block | Delete the lines that write `km_chart.b64`, run `base64 -D` into `Downloads/<name> chart.pdf`, run `ls -l` on it and call `emailFromPDF`. The PDF stays in the `b64` variable only. |
| `getChartPDF`: the `else` (manual fallback) block | Delete it: the marker file, the Downloads search and `base64 -i` on a hand-saved PDF. In its place, record "chart not attached" for this patient and carry on. The session is still set up, and the summary flags it. |
| `getChartPDF`: the `dl` and `outPath` variables | Delete. |
| `emailFromPDF` handler, `CHART_EMAIL` property | Delete. |
| `mainFlow`: email | If `JS_AMD_READ` found no email, run `JS_AMD_EMAIL` in `click` mode (opens Demographics) and then in `read` mode. Put the result in `A.email`. This code exists already but nothing calls it. |
| `H.phase2`: "add the email from the chart" step | Delete. Email is handled by the demographics step. |
| After `runPhase(… 'phase2' …)` | `set b64 to ""`, and in the Heidi page run `F = null` / `H.F = null`. |
| Report tab, before closing it | Run `window.__kmPdf = null`. |

### A2. Nothing on the clipboard

| Where | Edit |
|---|---|
| `on run`: both `set the clipboard to RUNLOG` blocks | Delete. If someone needs a log for troubleshooting, it's the PHI-free log file (A3). |

### A3. Logs with no patient data

**Rule:** a log line may contain step names, timings, counts, yes/no results and error *types*. It may never contain a name, DOB, email, AMD id, appointment date, search-result text or page text.

**AppleScript `addLog` call sites**

| Today | Becomes |
|---|---|
| `"AMD read: " & patientName & date & time & provider & ids` | `"AMD read: ok, provider kind=" & kind & ", email on chart=" & yes/no` |
| `"Opening upcoming appointment " & date & …` | `"Opening upcoming appointment from timeline"` |
| `"AMD name/DOB diagnostic: " & …` | `"AMD read failed: docs shown=n of m"` (counts only; see `JS_AMD_READ` below) |
| `"Typed date/time: " & …` | `"Date/time typed by user"` |
| `"Chart report patient id=… on-screen ids=…"` | `"Chart report id matches patient on screen: yes/no"` |
| `"Report PDF grabbed " & info` (has the report URL with patient id) | `"Report PDF grabbed (" & KB & " KB)"` |
| `"Saved to Downloads…"`, `"Using manually saved PDF…"` | Deleted, along with A1. |

**Page-side logs (`JS_HEIDI`'s `log()`, and `JS_AMD_READ`)**

| Today | Becomes |
|---|---|
| `H.start`: `'A=' + JSON.stringify(A…)` | `'start: provider=' + kind + ' email=' + (A.email ? 'yes' : 'no')` |
| `'search results: ' + texts` | Counts by reason only, e.g. `search results: 3 (exact 1, DOB differs 2)` |
| `'creating patient: ' + txt(opt)`, `'Create row … shows ' + text` | `'creating patient'`, `'Create row did not show the full name'` |
| `'asked about partial match -> ' + ans` | `'partial match: user picked #2'` or `'… created new'` |
| `'identifier box shows ' + value`, `'real typing gave ' + value` | `'identifier box mismatch, retyping'`, `'real typing mismatch, page typing used'` |
| `'warning: header shows ' + text` | `'warning: header missing first name'` |
| `'Past sessions rows: ' + labels` | `'Past sessions rows: ' + count` |
| `'did not stick; date button shows ' + text` | `'date did not stick'` |
| `startWatch()` (logs the date button every 120 ms) | Delete. |
| Demographics `'NOT filled (box shows …)'`, `'gender now …'` | `'<field>: filled / not filled'` (field name only). |
| `desc(el)` (used in click and failure logs) | Tag, role and size only. No `innerText`, value, `aria-label` or `title`, because those can hold names or file names. |
| `pageMap()` on every failure | Only when a `DEBUG` flag is on (off by default). Even then it records structure only (tag, role, position), never text. It goes to the page's DevTools console, not the log file. |
| `JS_AMD_READ` error payload: `around` text + `docDiag()` banner names | Return counts only: docs shown, docs total, banner found yes/no. |

**Safety net.** Apply both checks to every line (`addLog` in AppleScript, `log()` in JS):
1. **`redact()`** replaces dates (`\d{1,2}/\d{1,2}/\d{2,4}`), emails, AMD-style ids (5+ digits) and `LAST, FIRST` patterns with `[date]` / `[email]` / `[id]` / `[name]`.
2. **Final check before writing the log file.** If the log still contains the current patient's last name, first name, DOB or email, replace the whole log with `"[log withheld: contained patient data]"` and the step where it stopped.

**Log file.** Keep `~/Library/Logs/Heidi macro log.txt` (last run only, already overwritten each run). After these edits it contains no PHI.

### A4. Error messages are generic

Thrown errors can be saved by Keyboard Maestro's engine log. They become:

| Today | Becomes |
|---|---|
| `"No upcoming appointment found for " & identifier` | `"No upcoming appointment found for the patient on screen."` |
| `"Could not find \"" + want + "\" again in the search results"` | `"Could not find the chosen patient again in the search results."` |
| `"…Chart Print report (patient id X) does not match the patient on screen (Y)…"` | `"…Chart Print report does not match the patient on screen…"` |

On-screen banners and dialogs, such as "Is one of these the same patient?", can still show names. They are on screen only and never saved.

### A5. Generic notifications

| Today | Becomes |
|---|---|
| `display notification (patientName & "  •  " & date & time) with title "Adding Heidi session…"` | `display notification "Working…" with title "Heidi macro"` |
| `… "Heidi session ready ✓" subtitle "Existing patient"` (body has the name) | Body: `"Session ready"`. Subtitle: `"Existing patient"` or `"New patient + chart attached"`. |
| `"Save the chart PDF to Downloads…"` | Deleted, along with A1. |

### A6. Nothing saved back into the script file

`RUNLOG` and `CHART_EMAIL` are AppleScript **`property`** values. If the macro runs from a saved script or applet, AppleScript can write property values back into that file after a run, along with any PHI they hold.

- Make `RUNLOG` a `global` that is set at the start of `on run`, and set it to `""` at the end, including on error.
- `CHART_EMAIL` goes away with A1.
- Keep every other patient value (`A`, `F`, `b64`, `r`, `patientName`…) a local variable in its handler.

### A7. Clear what's left in the browser

| Where | Edit |
|---|---|
| Heidi page, after each phase (`pullHeidiLog`) | After pulling the log: `H.log = []; H.K = {status:'idle'}`. Remove the `km-banner`. |
| AMD page (`JS_AMD_PRINT`) | After the report URL is read, `removeAttribute('data-km-report')`, because it holds a URL with the patient id. |

### A8. Small items

- Chart report id check: the shell command `echo <url> | sed …` puts the report URL (with the patient id) in a process argument. Parse it in AppleScript with `text item delimiters` instead.
- `realMouseClick` writes `km_realclick.js` for each click. It contains no PHI, but write it once per run (this also speeds things up).
- Remove `emailFix`, `joinText` (if unused once A1 is done) and the dead `day-then-time` branch.

---

## Part B: SDM form (in this repo)

| File | Edit |
|---|---|
| `app/index.html:426` (`#notes`) | Add `autocorrect="off" autocapitalize="off" spellcheck="false"`, so the iPad keyboard doesn't learn words typed about patients. |
| `app/index.html:982` (the "Describe" field) | Same attributes. |
| `app/sw.js` and the version label | Bump to v24, so iPads pick up the change. |
| `docs/STAFF_SOP.md` step 11 | Add: "then in Files › **Recently Deleted**, delete it again (iPad keeps deleted files 30 days)". |
| `docs/IPAD_SETUP.md` | Add a daily check: empty Files › Recently Deleted. Set notification previews to "When Unlocked". |
| `docs/CLINIC_INTEGRATION_PLAN.md` §3 | Add the Recently Deleted step to the "Local files" row. |

---

## Part C: one-time cleanup on the clinic Mac (before using the new version)

1. Delete every `* chart.pdf` in **Downloads**, then empty the Trash.
2. Delete `~/Library/Logs/Heidi macro log.txt`.
3. Clipboard history: clear it in Keyboard Maestro (Clipboard History Switcher → Clear) and in any other clipboard app.
4. Notification Center: clear the old "Adding Heidi session…" notifications.
5. Replace the saved script or applet with the new version, so any PHI in old saved properties goes with it.
6. **Time Machine:** older backups may hold these files. Either keep the backup disk encrypted and let the copies age out, or, if your macOS version offers it, delete them from backups (in Time Machine, select the file → Delete All Backups of…).

---

## Part D: clinic settings (not code)

| Item | Action |
|---|---|
| BAAs | Confirm signed BAAs with **Heidi Health** and AdvancedMD. |
| Chrome | Use a dedicated profile for AMD and Heidi with **sync off**. Or confirm your Google Workspace BAA covers Chrome sync. |
| Mac | FileVault on. Auto-lock ≤ 5 min. Time Machine backup encrypted. Notification previews "When Unlocked". |
| Clipboard apps | Exclude Chrome and Script Editor/Keyboard Maestro from clipboard history, or turn history off. |
| Screenshots and logs in chats | Crop or blur patient names and DOBs before sharing with any outside tool, Claude included, unless a BAA covers it. |
| Risk analysis | Add the macro and the SDM form workflows to the Security Risk Analysis. |

---

## Part E: how to check it worked (use a **test patient** only)

After one run on a test patient, all of these should come back empty:

```sh
TEST="Testpatient"   # the test patient's last name
grep -ril "$TEST" ~/Library/Logs ~/Downloads "$TMPDIR" 2>/dev/null
pbpaste | grep -i "$TEST"
mdfind "$TEST"
grep -al "$TEST" /path/to/the/saved/macro.scpt   # script file holds no saved values
ls ~/Downloads/*chart.pdf 2>/dev/null
```

Then check by eye:
- Notification Center has no names.
- Keyboard Maestro's clipboard history has nothing new.
- In Heidi, the patient's demographics and attached chart are correct.

---

## Order of work

1. **Part C** cleanup: today, no code needed.
2. **Part A**: one new macro version (v20) with A1–A8. I need the latest copy of the script (the v19 that was pasted, unless it has changed since).
3. **Part B**: SDM form edits. These can be done here and pushed right away.
4. **Part E**: test with a test patient.
5. **Part D**: clinic settings, alongside.

The functional changes in `HEIDI_MACRO_PLAN.md` (template fix, demographics for everyone, chart date range) can go into the same v20, or a later version.
