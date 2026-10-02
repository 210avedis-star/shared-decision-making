# Heidi – Add Upcoming Session: Simplification Plan

**Goal:** The macro reads a patient's upcoming appointment in AdvancedMD (AMD), then sets up the Heidi session for it: patient linked, demographics current, the right note template, date and time set, and the chart attached as context. Later it should run unattended every morning for every patient on the schedule.

**Rules (same as the SDM form):** HIPAA compliant. No patient data is saved anywhere except AMD and Heidi, which are both covered by BAAs. That means no files, logs, clipboard contents or notifications with PHI.

---

## 1. Summary of changes

| # | Change | Why |
|---|---|---|
| 1 | Sync demographics for **every** patient, not only new ones | Requested. Heidi stays in step with AMD. |
| 2 | Set the template on the **Note** tab. Stop using + → Create a document. | That path makes the extra AI "Outpatient Consultation" documents. |
| 3 | Decide Dr. Hey vs. PA from the scheduled-provider field only | Stops a PA visit getting Dr. Hey's template. |
| 4 | Chart Print from the **last Hey/PA clinic, AAI or Op note → today**, max 200 pages | Requested. The PDF gets smaller and the run gets faster. |
| 5 | Attach the chart for every patient, not only new ones | Approved. |
| 6 | No PDF, log, clipboard or notification with PHI | HIPAA. Today the macro breaks this rule in 5 places (§4). |
| 7 | Cut dead code, fixed waits and per-click helper scripts | Speed and maintainability. |
| 8 | Unattended morning run with Playwright (§5) | Runs while the Mac is locked. |

---

## 2. Requested fixes

### 2.1 Demographics for all patients

Today the *fill in the new patient details* step only runs `if (isNew)`, and `mainFlow` returns before phase 2 for existing patients. The email step also leaves an existing different email alone.

**Plan**
- Rename the step to **Sync demographics** and run it for every patient after the patient is linked.
- Fields: First name, Last name, DOB, Gender, Email. AMD is the source of truth. If a Heidi field differs, it is overwritten. If the AMD value is empty, the Heidi value is kept, never blanked.
- Get the email from AMD's **Demographics** screen. `JS_AMD_EMAIL` already has a `click`/`read` mode for this that nothing calls. This replaces reading the email out of the PDF, which needed the PDF on disk.
- Confirm Heidi shows "Saved" after each field. The log lists which *fields* changed, never their values.

### 2.2 Correct note template

Correct templates, from the screenshots:

| Provider | Template (exact name) | Where it is in Heidi's picker |
|---|---|---|
| Dr. Hey | `HC Outpatient Consultation Note` | Favourites |
| MA (and anyone else) | `PA Outpatient Consultation Note` | Created by You |

**What the screenshot shows.** The two "Outpatient Consultation" tabs with the sparkle icon are AI-generated **documents**, not the note. The macro makes them with **+ → Create a document**, then types the template name into "Search or generate anything". Heidi treats that as a request to *generate* a document and gives the tab a shortened title. The **Note** tab is untouched and keeps its default template.

There are two of them because of the duplicate check. The macro checks for a tab whose name *starts with* "HC Outpatient Consultation Note" (or "PA Outpatient Consult"). The tab is titled "Outpatient Consultation", so that check never passes. The step reports failure, and the next attempt or re-run adds another document.

**Fix**
1. Remove the **+ → Create a document** path completely.
2. On the **Note** tab, click its template button (the one showing "Goldilocks" in your earlier screenshot). Search for the template, then click the item whose name matches **exactly**. Leave "Set as default" off.
3. Confirm that the Note tab's template button now shows the chosen name. The diagnostic run also checks whether "Auto" can change it afterwards.
4. Clean-up: if a run finds sparkle "Outpatient Consultation" documents that an earlier version made, it reports them. It doesn't delete them, because deleting is for a person to do.

**Provider check (separate, but also affects which note).** `JS_AMD_READ` combines *every* AMD field whose id contains "rovider". If a billing provider field says Hey on a PA visit, the PA visit gets Dr. Hey's template. **Fix:** read only the appointment's scheduled provider (the diagnostic run finds that field). Dr. Hey → HC note, anyone else → PA note.

### 2.3 Chart Print since the last clinic visit

**Last clinic visit** = the date of the most recent of these notes in AMD:
- a Hey or PA clinic note,
- an AAI note,
- an Op note.

The diagnostic run lists the note *type names* (not patient content) exactly as AMD shows them. You confirm which names count, and the macro matches only those.

**Plan**
- Find the newest qualifying note date in the AMD chart's notes list.
- In Chart Print's **Load Report Setup**, set **From = that date** (the whole day, so all of that visit is included) and **To = today**. Documents filed since then (imaging, outside records) fall in the range.
- No qualifying note (a new patient): print the whole chart.
- **200-page cap.** The page count is read from the PDF in memory. Over 200 pages, the macro keeps the **most recent 200** (oldest pages dropped) using the pdf-lib library, bundled with the script (not loaded from the internet). Which end of the PDF is "most recent" depends on Chart Print's order; the diagnostic run checks. The log records only "trimmed N → 200 pages".
- Keep the existing check that the report's patient id matches the patient on screen.

---

## 3. Simplify and speed up

| Area | Today | Change |
|---|---|---|
| Flow | 2 phases. Existing patients stop after phase 1. | 1 flow for everyone: AMD read → Heidi (link, demographics, template, chart, context, date/time last). |
| Overlap | AMD Chart Print starts only after Heidi phase 1 finishes. | Start the AMD Chart Print fetch in the AMD tab *while* Heidi phase 1 runs. It's JS-only and doesn't need focus. |
| Fixed waits | Roughly 10–15 s of fixed `sleep`s per patient (800, 1500, 1600, 2000, 2500, 3000 ms …). Failed date steps redo the whole attempt. | Wait for the real condition instead (element present, DOM quiet for 300 ms, "Saved" shown). Keep short sleeps only where Heidi needs them. |
| Date/time | Two modes. `day-then-time` is never called (dead). A 120 ms watcher logs every change. | Keep `time-then-day` only. Drop the watcher, or make it debug-only. |
| Real clicks | Writes a JXA file and runs `osascript` for **every** click. | Write the helper once per run, or run it inline with `osascript -e`. |
| PDF transfer | Full chart in base64, passed through AppleScript strings into Heidi. Slow for big charts. | A since-last-visit PDF is much smaller. Pass it in chunks if it's still large. |
| Email | Reads AMD text, then writes the PDF to disk and parses it with PDFKit. | Read the AMD Demographics screen only. |
| Dead code | `emailFix`, `CHART_EMAIL` plumbing, `JS_AMD_EMAIL` unused, `TA` in `JS_AMD_READ`, `pre` in phase 2, the manual "save to Downloads" fallback. | Remove, or wire up where noted above. |
| Diagnostics | `pageMap()` dumps 160 elements with their text, and `docDiag()` logs banner names, on every failure. | Debug flag only, with text redacted (structure, roles and ids only). |

---

## 4. HIPAA gaps in the current code (all fixed by this plan)

| Current behaviour | Risk | Fix |
|---|---|---|
| Saves `<name> chart.pdf` to **Downloads** ("keep a copy") | PHI on disk, possibly synced by iCloud | Never write the PDF. It stays in memory only, from AMD tab → Heidi tab. |
| Writes the base64 PDF to `km_chart.b64` in temp items | PHI on disk | Remove. |
| Saves `RUNLOG` to `~/Library/Logs/Heidi macro log.txt` (name, DOB, sex, search results, page text) | PHI on disk | Log step names, timings and error *categories* only. A `redact()` pass runs on every line. |
| Copies the log to the **clipboard** every run | PHI on clipboard; Universal Clipboard can sync it to other devices | Remove. |
| Notifications show patient name and appointment time | Shown on the lock screen; kept in Notification Center | Generic text only ("Heidi session ready", or "3 of 24 need attention"). |
| Manual fallback: "save the chart PDF to Downloads" | PHI on disk | Remove. Flag the patient instead. |

Also: clear `window.__kmH.log` and the PDF data in the page after each patient, and close the report tab (already done).

---

## 5. Path to the unattended morning run

1. **Unattended mode flag.** Any place that now calls `need()`, shows a banner or opens a dialog skips that patient and records why. Examples: an ambiguous patient match, an unknown provider, a step that failed twice. It never guesses a patient match.
2. **Schedule loop.** Read the day's schedule in AMD and run the flow once per appointment, using the same per-patient code as the manual macro.
3. **No duplicates.** Before creating a session, check Heidi's session list for this patient at this date and time. Skip it if it's already there, so a re-run is safe.
4. **Trusted input without a screen.** See §5a.
5. **Logins.** If AMD or Heidi is logged out, stop the run and send a generic notification asking staff to log in. Don't store passwords in the script.
6. **Scheduling.** Use `launchd` at a fixed early time, with a `pmset` wake scheduled shortly before it.
7. **Morning summary.** Show counts plus the appointment *times* that need attention, e.g. "8:15, 10:45: unknown provider". Show it on screen or in a notification only. Nothing is written to disk.

Optional: ask Heidi whether their partner API can create sessions and attach documents, and check AMD's API. Either would replace most of the UI automation.

### 5a. Playwright: what it is and what changes

**What it is.** Playwright is a free, open-source tool from Microsoft for controlling Chrome from a script. It's widely used for automated website testing. Here it would run on the clinic Mac as a small Node.js program, in place of the AppleScript.

**Why it's needed.** The AppleScript sends "real" keystrokes and mouse clicks through macOS (System Events and CGEvent). Heidi's patient search and date picker ignore clicks that a web page fakes, which is why those real inputs are there. But macOS blocks them while the screen is locked, and HIPAA requires an auto-lock. Playwright sends the same trusted input straight into Chrome through Chrome's own automation channel, so it works with the screen locked.

**How a morning run works**
1. `launchd` (the Mac's built-in scheduler) wakes the Mac and starts the script, for example at 6:00.
2. The script opens a dedicated Chrome profile used only for this job. It's logged in to AMD and Heidi.
3. It reads the day's schedule in AMD. For each appointment, it does what the macro does now: read the patient, get the chart PDF, then link the Heidi patient, sync demographics, set the template, attach the chart, set the date and time.
4. At the end, a generic notification shows the counts and the appointment *times* that need a person.

**What gets simpler**
- No AppleScript poll loop, no System Events typing, no JXA click helpers. Typing and clicking are one-line calls.
- **The chart PDF never touches the disk or AppleScript strings.** It goes from AMD into the script's memory, then into Heidi's file input as an in-memory file. That's simpler, faster and safer than today.
- The 200-page trim runs in the script's memory with pdf-lib.
- Most of the page logic (the finders and steps in `JS_HEIDI`) is reused as-is.
- Waiting for conditions ("search results loaded", "Saved") is built in, which replaces most fixed sleeps.

**Security**
- Everything stays on the clinic Mac. The only network traffic is to AMD and Heidi, same as now. No cloud service or third party is involved.
- Playwright talks to Chrome through a private pipe, not a network port, so nothing else can connect to that Chrome.
- The dedicated Chrome profile stores only login cookies, as Chrome does now. Turn on FileVault, and turn off Chrome sync for that profile.
- No logs with PHI, no files, no clipboard (same rules as §4).

**Setup (one time, about an hour)**
1. Install Node.js and Playwright on the clinic Mac.
2. Open the dedicated profile once and log in to AMD and Heidi.
3. Install the `launchd` job and a `pmset` wake time.
4. Run it on one day's schedule while someone watches.

**Main risk: logins.** If AMD or Heidi logs out every night or asks for 2-factor each morning, the run can't start by itself. Then the fallback is a one-click start: the first person in logs in and clicks "Run today's sessions", and it runs in the background while they work. We find out how long logins last in the first week.

**What stays.** The AppleScript stays as the manual one-patient macro (with the §4 HIPAA fixes) until the Playwright version is proven.

---

## 6. Rollout

1. **Diagnostic run (one time, shown on screen, nothing saved).** On one test patient:
   - the id and label of each AMD provider field, to pick the scheduled one;
   - the note type names in the AMD notes list, so you can confirm which count as Hey/PA clinic, AAI and Op notes;
   - the labels and control types of the Chart Print setup panel, and whether Chart Print lists oldest or newest first;
   - the Note tab's template button and picker, and whether "Auto" changes a chosen template.
2. Quick fixes in the current AppleScript: the HIPAA items (§4), the Note-tab template, the provider field, demographics for everyone.
3. Build the Playwright version (§5a) with the chart date range, 200-page cap and schedule loop.
4. Test with test patients: new, existing, Dr. Hey visit, PA visit, no prior note, a chart over 200 pages, a different email in Heidi.
5. Run it on one day's schedule while someone watches. Then turn on the `launchd` schedule.
6. Put the code under version control. It contains no PHI.

---

## 7. Decisions

| # | Question | Answer |
|---|---|---|
| 1 | Attach the chart for existing patients? | **Yes.** |
| 2 | Wrong note | Answered by the screenshot: it's the extra AI documents (§2.2). |
| 3 | What sets "last clinic visit"? | **Last Hey/PA clinic note, AAI note or Op note.** Exact AMD names confirmed in the diagnostic run. |
| 4 | Chart size | **Cap at 200 pages**, keeping the most recent. |
| 5 | Provider names | No answer needed. The diagnostic run reads them. |
| 6 | Playwright | Details in §5a. Waiting on your OK. |
| 7 | Overwrite differing Heidi demographics with AMD values? | Recommended yes; never blank a field. Waiting on your OK. |
