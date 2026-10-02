# Heidi – Add Upcoming Session: Simplification Plan

**Goal:** The macro reads a patient's upcoming appointment in AdvancedMD (AMD), then sets up the Heidi session for it: patient linked, demographics current, the right note template, date and time set, and the chart attached as context. Later it should run unattended every morning for every patient on the schedule.

**Rules (same as the SDM form):** HIPAA compliant. No patient data is saved anywhere except AMD and Heidi, which are both covered by BAAs. That means no files, logs, clipboard contents or notifications with PHI.

---

## 1. Summary of changes

| # | Change | Why |
|---|---|---|
| 1 | Sync demographics for **every** patient, not only new ones | Requested. Heidi stays in step with AMD. |
| 2 | Pick the template on the **Note** tab and match the full exact name | Fixes the wrong note for MA and Dr. Hey visits. |
| 3 | Decide Dr. Hey vs. MA from the one scheduled-provider field only | The MA mix-up most likely starts here. |
| 4 | Chart Print limited to **last clinic visit → today** | Requested. The PDF gets smaller and the whole run gets faster. |
| 5 | Attach the chart for every patient, not only new ones | Follows from #4. Needs your OK (see §7). |
| 6 | No PDF, log, clipboard or notification with PHI | HIPAA. Today the macro breaks this rule in 5 places (§4). |
| 7 | Cut dead code, fixed waits and per-click helper scripts | Speed and maintainability. |
| 8 | Add an "unattended" mode: never wait on a person; skip and flag the patient instead | Needed for the morning run. |

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

Likely causes of the wrong note, in order:
1. **Provider detection.** `JS_AMD_READ` joins *every* field whose id contains "rovider" (`prov.join(' / ')`). On an MA visit, a billing or rendering-provider field often still says Hey, so the `hey` regex matches and the MA visit gets Dr. Hey's template. **Fix:** read only the scheduled column/resource field. Find its exact id in the diagnostic run (§6). Classify by exact name, using a short list: Hey → HC note, known MAs/PAs → PA note. An unknown provider is asked about when attended, or skipped and flagged when unattended.
2. **Wrong place in Heidi.** The macro adds a *second* document via **+ → Create a document**. The default **Note** tab keeps its own template (the "Goldilocks" button beside "Auto" in the screenshots), and that tab is the note people see. **Fix:** open the template picker on the Note tab itself, choose the template, then confirm the button now shows the template name. Leave "Set as default" off. Check in the diagnostic run whether "Auto" overrides a chosen template.
3. **Loose matching.** `TPL_OTHER = "PA Outpatient Consult"` is matched as a prefix. **Fix:** use the full names above and an exact (normalized) match. If not exactly one item matches, stop.

### 2.3 Chart Print since the last clinic visit

**Plan**
- **Last clinic visit** is the most recent *past* office appointment, including the whole day of that visit. Read the "Last:" date from the AMD banner the same way "Next:" is read now. If the banner has no "Last:" date, use the most recent past appointment on the timeline. Phone calls and surgery dates don't count, unless you'd like them to.
- In Chart Print's **Load Report Setup** panel, set **From = last visit date** and **To = today**, then Print. Documents filed after the visit, such as imaging and outside records, fall in that range and are included.
- No prior visit (a new patient): print the full chart. A size or year cap is optional (§7).
- Keep the existing safety check that the report's patient id matches the patient on screen.
- The setup panel's field names aren't known yet. The diagnostic run (§6) records the panel's labels and control ids, with no PHI.

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
4. **Trusted input without a screen.** The macro now relies on System Events keystrokes and CGEvent mouse clicks. Those **don't work while the Mac is locked**, and an auto-lock is a required safeguard. For the scheduled version, drive Chrome through the DevTools protocol, using Playwright with a dedicated Chrome profile on the clinic Mac. It sends trusted keystrokes and clicks to the page itself, so the screen can stay locked. The page-side logic (the finders and steps in `JS_HEIDI`) carries over almost unchanged.
5. **Logins.** If AMD or Heidi is logged out, stop the run and send a generic notification asking staff to log in. Don't store passwords in the script.
6. **Scheduling.** Use `launchd` at a fixed early time, with a `pmset` wake scheduled shortly before it.
7. **Morning summary.** Show counts plus the appointment *times* that need attention, e.g. "8:15, 10:45: unknown provider". Show it on screen or in a notification only. Nothing is written to disk.

Optional: ask Heidi whether their partner API can create sessions and attach documents, and check AMD's API. Either would replace most of the UI automation.

---

## 6. Rollout

1. **Diagnostic run (one time, no PHI saved).** On one test patient, the debug mode shows on screen, not on disk:
   - the id and label of each AMD provider field, to pick the scheduled one;
   - the labels and control types of the Chart Print setup panel;
   - whether the banner shows a "Last:" date;
   - the Note tab's template button and the picker's structure, and whether "Auto" changes a chosen template.
2. Build step 1 changes (fixes, HIPAA, simplification) in the current AppleScript. Test on test patients: a new patient, an existing one, a Dr. Hey visit, an MA visit, a patient with no prior visit, and one with a different email in Heidi.
3. Measure time per patient, before and after.
4. Add the unattended mode and run it on a single day's schedule while someone watches.
5. Move to the Playwright runner and `launchd` schedule (§5.4–5.6).
6. Put the macro under version control. The script contains no PHI, so it can go in a repo like this one.

---

## 7. Decisions needed

1. **Chart for existing patients:** attach the since-last-visit chart to *every* session? (Recommended: yes.)
2. **Overwrite in Heidi:** may AMD values replace different Heidi values for name, DOB, gender and email? (Recommended: yes. Never blank a field.)
3. **"Last clinic visit":** office visits only, or also surgery or post-op dates?
4. **No prior visit:** full chart, or a cap (for example, the last 2 years)?
5. **Provider list:** names exactly as AMD shows them for Dr. Hey and for each MA/PA.
6. **Unattended runner:** OK to move the scheduled version to Playwright on the clinic Mac (§5.4)?
