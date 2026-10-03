# Task 4: Feature changes (v21–v23)

Do these **after v20** (HIPAA fixes and test mode in `EDITS.md`) passes the test loop. Each version is tested with the shared loop in `TESTING.md` before the next one starts.

| Version | What | Needs first |
|---|---|---|
| **v21** | Demographics for every patient. Chart attached for every patient. Correct note template. Correct Dr. Hey vs PA choice. | Diagnostics D1, D2 |
| **v22** | Chart download from the last clinic visit only, 200-page cap | Diagnostics D3, D4, and two answers from the person |
| **v23** | Faster: fewer tab switches, waits that end when ready instead of fixed sleeps | v22 passing |
| later | Runs by itself every morning for every patient | Separate project (§6). Not started until the person approves. |

The rules in `CLAUDE.md` and `TESTING.md` apply throughout: test patient only, never look at pages yourself, never weaken a safety feature.

---

## 1. Diagnostics (build these first, in v21)

Some page details aren't known yet: the Heidi template picker, the AMD provider field, the AMD notes list and the Chart Print setup panel. Add a diagnostic mode so the macro can describe them **without capturing patient data**:

```
osascript macro.applescript --test <TestLast> --diag <name>
```

A diagnostic only reads. It never clicks Save or creates anything, except where noted below. It writes its output to `testkit/reports/heidi-session/diag-<name>.md`, and the leak check runs on that file too.

| Name | Reads | Must not output |
|---|---|---|
| **D1 `heidi-template`** | In a **test patient's** Heidi session: <ul><li>the Note tab's toolbar buttons (tag, role, aria-label, text, e.g. "Auto", "Goldilocks");</li><li>after clicking the template button, the picker dialog's search box, section headings ("Favourites", "Created by You") and item names.</li></ul> Template names aren't patient data. Close the picker with Escape. | Anything outside the toolbar row and the picker dialog (for example the sidebar session list). |
| **D2 `amd-provider`** | On the open appointment, every `select`/`input`/`span` whose id or nearby label mentions "provider": its **id**, its **label**, and the selected value (staff names aren't patient data). | Any other page text. |
| **D3 `amd-notes`** | The chart's notes or encounter list: the **unique note type or template names** and how many of each. No dates, no note content. | Dates, note text, banner. |
| **D4 `amd-chartprint`** | Opens Chart Print's **Load Report Setup** panel and lists its labels, control types and ids (date fields, filters, checkboxes), then closes it **without printing**. | Anything outside the panel. |

The person reviews each `diag-*.md` before Claude uses it.

---

## 2. v21: demographics, chart and template

### 2.1 Demographics for every patient

- **Goal:** every run updates the Heidi patient's details from AMD (first name, last name, DOB, gender, email), not only for new patients.
- In `H.phase1`, remove the `if (isNew)` around the **"fill in the new patient details"** step and rename it **"sync demographics"**.
- **Rules:**
  - AMD is the source of truth. If a Heidi field differs, overwrite it.
  - If the AMD value is empty, leave Heidi's value alone. Never blank a field.
  - Log only the field name and `same / updated / not filled`.
  - After each field, wait for Heidi's "Saved" label (`inputFor()` already matches `Saved|Saving`) instead of a fixed `sleep(500)`.
- The email now comes from `A.email` (v20 reads it from AMD Demographics). Delete the `if (F.email)` email step in `H.phase2`.
- *Person to confirm:* overwriting different Heidi values with AMD values. That's the recommended setting.

### 2.2 Chart attached for every patient (approved)

- In `mainFlow`, remove the early `return` for existing patients. Every patient goes through the chart and phase 2.
- **Dated file name, so a new chart never counts as "already attached":** in `JS_AMD_READ`, `out.fileName = out.identifier.toLowerCase() + ' chart ' + <today YYYY-MM-DD> + '.pdf'`. `hasFile()` in `H.phase2` then only matches today's chart.
- The context step ticks only today's chart.

### 2.3 Correct note template (the extra "Outpatient Consultation" tabs)

**What goes wrong in v19/v20.** The template step clicks **+ → Create a document** and types the template name into "Search or generate anything". Heidi treats that as *generating* an AI document, which is the sparkle-icon tab titled "Outpatient Consultation". The real **Note** tab never changes and keeps its default template.

The "already there" check looks for a tab starting with the full template name, so it never matches the shortened title. Each retry or re-run adds another tab.

**New behavior**
1. Delete the whole **+ → Create a document** path from the template step.
2. On the **Note** tab, click its **template button**: the button in the Note toolbar that shows the current template name, next to "Auto". D1 confirms how to find it.
3. In the picker, type the template name into the search box and click the item whose text **exactly** equals the name. Normalize case and spaces; no prefix match. If 0 or more than 1 items match, fail with `template not found` or `template ambiguous`.
4. **Never** touch the "Set as default" toggle.
5. **Check it worked:** the Note tab's template button now shows the chosen name. Log `Note template set: yes/no` (template names are fine to log).
6. If D1 shows that "Auto" can override a chosen template, make sure "Auto" is off. If it's unclear, fail and report.
7. Don't delete the AI "Outpatient Consultation" documents earlier runs made. Log `old AI documents present: N` so the person can remove them.

**Template names.** Replace these properties:
```applescript
property TPL_HEY : "HC Outpatient Consultation Note"
property TPL_OTHER : "PA Outpatient Consultation Note"
```

### 2.4 Correct Dr. Hey vs PA choice

- **What goes wrong:** `JS_AMD_READ` joins **every** field whose id contains "rovider" (`prov.join(' / ')`). A billing or rendering provider field that says Hey makes a PA visit look like Dr. Hey's.
- **New behavior:** read **only** the appointment's scheduled-provider field, using the id from D2. Then:
  - name matches Hey → `TPL_HEY`;
  - any other provider → `TPL_OTHER`;
  - empty or not found → in test mode, fail with `provider not read`; in normal mode, ask as today.
- Log `provider kind=hey|other`. The staff name may be logged; it isn't patient data.

### 2.5 v21 tests (add to `heidi-session/test.conf`)

| Case | Setup | Expected |
|---|---|---|
| `A` existing, Dr. Hey appointment | Test A, appointment with Dr. Hey | `Outcome: existing patient`, demographics `same/updated` lines, `Note template set: yes` with HC, chart attached (`PDF received:`), no new sparkle tab |
| `P` existing, PA appointment | Test A has a second appointment with the PA. The person opens it. | `provider kind=other`, `Note template set: yes` with PA |
| `D` changed demographics | The person changes Test A's email in Heidi to something else first | `Email: updated` |

---

## 3. v22: chart since the last clinic visit, max 200 pages

**Goal.** Chart Print covers from the date of the most recent qualifying note through today, including that whole day. The qualifying notes are:
- a Dr. Hey or PA clinic note,
- an AAI note,
- an Op note.

**Needs from the person first**
1. From the D3 list, which note type names count (exact names).
2. Whether Chart Print puts the newest pages first or last. The person checks one printed test chart by eye.

**Behavior**
1. In AMD, find the newest note whose type is in the approved list. Use its date as **From** and today as **To**.
2. Set those in Chart Print's Load Report Setup, using the fields from D4, then Print.
3. No qualifying note (a new patient): print the full chart.
4. **200-page cap**, measured in the report tab after the PDF is fetched in `JS_REPORT_PDF`:
   - Count pages in memory.
   - If there are more than 200, trim to the **most recent 200** with **pdf-lib**. Load it from a local copy in the project (`vendor/pdf-lib.min.js`, read by AppleScript and injected into the report tab), never from the internet.
   - First check that `execute javascript` can run it in the report tab. If the page blocks it, stop and report; don't try a workaround.
5. Log only `chart range: last-visit | full`, `pages: N`, `trimmed: yes/no`. No dates.
6. Keep the existing check that the report's patient ID matches the patient on screen.

**Tests**

| Case | Expected |
|---|---|
| `A` (Test A has a qualifying note) | `chart range: last-visit`, page count smaller than a full print |
| `N` (new patient, no notes) | `chart range: full` |
| `T` (a test chart over 200 pages, if one can be made) | `pages: 200`, `trimmed: yes` |

---

## 4. v23: faster

**Goal:** the same results in less time per patient. Measure with the test loop's `Duration`, using the v22 time as the baseline. Every change must still pass all cases. If a change causes any new failure, undo it.

1. **Do all the AMD work first, then all the Heidi work in one pass:** AMD read → email → Chart Print → PDF, then one Heidi phase. That's one switch between tabs instead of four, and one library injection. Merge `phase1` and `phase2` into one `H.run` with the same steps in the same order.
2. **Replace fixed sleeps with waits that end when ready**, using `waitFor()` on the real condition (element present, the page has stopped changing for 300 ms, "Saved" shown). Start with the biggest:

   | Sleep | Where | Wait for |
   |---|---|---|
   | `sleep(800)` | after New session | identifier box present |
   | `sleep(1500)` | before typing the last name | identifier box focused and enabled |
   | `sleep(1600)` | after the search dropdown appears | results list stops changing for 300 ms |
   | `sleep(2000)` | before the date step | patient panel closed and date button present |
   | `sleep(2500)` | after the day click | date button shows the new date, or editor closed |
   | `sleep(3000)` + full retry | date step failure | retry only the failed part |
   | `sleep(500)` per field | demographics | "Saved" label |

   Change **one or two at a time** and run the loop after each.
3. **Write the click helper once:** `realMouseClick` writes `km_realclick.js` on every click. Write it once per run, and reuse it.
4. **Remove dead code:** the `day-then-time` branch of `setDateTime` (it's never called), `pre` in `H.phase2`, the unused `TA` in `JS_AMD_READ`, `docDiag()` if it's unused after v20, and `joinText` if unused.
5. **Report:** the report lists the duration for each case before and after.

---

## 5. Definition of done (v21–v23)

- All cases in `heidi-session/test.conf` pass, including the new ones here, with every leak check passing.
- Clearly faster per patient than v22, with no new failures.
- A person does one normal Keyboard Maestro run on Test A.
- A person spot-checks the result in Heidi: the Note tab shows the right template, no new sparkle tabs, today's chart is in Files and used as context, and the demographics are correct.

---

## 6. Later: runs by itself every morning (don't start yet)

The aim is a scheduled run each morning for every patient on the day's schedule. It needs a different way to drive Chrome (Playwright). The macro's real keystrokes and clicks can't work while the Mac is locked, and the screen must lock for HIPAA.

**Waiting on the person's approval.**

When approved, the plan is:
- Reuse the page logic from v23.
- Read the day's AMD schedule.
- Run the same flow per patient.
- Skip a patient and flag it instead of waiting for a person.
- Never create duplicate sessions.
- Finish with a summary showing only appointment times.

The v20 test mode and the fail-fast behavior already make the macro ready for this.
