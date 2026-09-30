# Shared Decision Making Form: Clinic Integration Plan

**Goal:** In surgery consults, the surgeon goes through the Shared Decision Making (SDM) form with the patient on an exam-room iPad. The completed form goes into the patient's chart in AdvancedMD as a document that prints cleanly on letter paper. Patient data must not be stored or sent anywhere except the EHR.

Source file: `form/shared_decision_form.html` (version 13, unchanged).

---

## 1. What the form does today (audit)

| Check | Result |
|---|---|
| External network requests (scripts, fonts, analytics, images) | **None.** The logo is embedded, and there are no `http(s)://` references, `fetch` calls or XHR. |
| Browser storage (`localStorage`, `sessionStorage`, IndexedDB, cookies) | **None.** All data lives only in the open page's memory. |
| Form submission to a server | **None.** No `<form action>`. |
| Output | `window.print()` with a two-page letter print stylesheet. |
| Signatures / initials | Drawn on `<canvas>` and printed as images. |

**Conclusion:** the form is already a *zero-persistence, zero-transmission* tool. The HIPAA work is mostly about **how the file gets onto the iPad, how the iPad is locked down, and how the PDF travels to AdvancedMD.** It is not about the form's code.

A note on "100% HIPAA compliant": HIPAA compliance belongs to the clinic's processes (a risk analysis, policies, training, BAAs and device safeguards), not to a single file. This plan makes the form add **no new place where PHI is stored or sent**, and it covers the remaining handling steps. Record this workflow in the clinic's HIPAA Security Risk Analysis.

---

## 2. Recommended architecture

```
 ┌──────────── Exam-room iPad (MDM-managed, passcode, encrypted) ───────────┐
 │                                                                          │
 │  SDM form (static HTML, runs 100% offline, no network allowed by CSP)    │
 │        │ fill + initials + signatures (in memory only)                   │
 │        ▼                                                                 │
 │  "Export PDF" → iPad print sheet → PDF                                   │
 │        │                                                                 │
 │        ├─► Upload straight into AdvancedMD patient chart (Option A)      │
 │        │   └─ AdvancedMD already covered by the clinic's BAA             │
 │        └─► or AirDrop to the front-desk Mac → upload (Option B)          │
 │                                                                          │
 │  Form wipes itself after export / on idle / when the tab is closed       │
 └──────────────────────────────────────────────────────────────────────────┘
                 PHI's only destination:  AdvancedMD chart
```

### 2.1 Getting the form onto the iPad without a data-collecting website

The form never needs to *send* anything, so the only question is how the iPad **loads the code**. iPadOS Safari will not run an HTML file opened from the Files app (Quick Look shows it without JavaScript). The realistic options, from simplest to most locked-down:

| Option | How it works | PHI exposure | Effort |
|---|---|---|---|
| **1. Offline web app (recommended)** | Host the static file on a clinic-controlled static location (internal server, or a static host). On each iPad, open it once and use **Add to Home Screen**. A small service worker caches it, so after that it runs **with Wi-Fi off**. A strict Content-Security-Policy (`connect-src 'none'; form-action 'none'`) makes the browser *block* any attempt to send data. | None. The host only serves a blank template, the same as an app store serving an app. Nothing typed ever goes back. | Low |
| **2. Offline web app on the clinic LAN only** | Same as option 1, but served from a machine inside the clinic that isn't reachable from the internet. | None | Low–medium |
| **3. Native wrapper app** | A tiny iOS app that bundles the HTML inside a WKWebView, with no website at all. It's distributed privately through Apple Business Manager (Custom App) or your MDM. | None | Medium (needs an Apple Developer account and a build step) |

Recommendation: **option 1 or 2 now**, and move to option 3 only if you want to remove the hosting step entirely. All three use the same HTML file, so nothing gets rewritten.

"On command" access: a Home Screen icon opens the form full-screen. Optionally, turn on **Guided Access** (Settings → Accessibility) so a patient can't leave the form or open other apps while holding the iPad.

---

## 3. Export to AdvancedMD

AdvancedMD is cloud-hosted, and the clinic should already have a BAA with them. It supports attaching documents such as PDFs to a patient's chart. Confirm the exact menu path and allowed file types with your AdvancedMD admin, because it varies by edition and configuration.

**Option A: upload from the iPad (fewest hops, preferred)**
1. The surgeon taps **Mark Complete**, the form validates, and the print sheet opens.
2. In the print sheet: **Share → Save to Files → "On My iPad / SDM Export"**. Don't use iCloud Drive.
3. Staff log in to AdvancedMD in Safari on the same iPad, open the patient's chart, attach the PDF and categorize it (for example, "Consent / Shared Decision Making").
4. Delete the local PDF. The form clears itself for the next patient.

**Option B: hand-off to a workstation**
- AirDrop the PDF to the front-desk Mac. This is encrypted and peer-to-peer, and nothing is stored in the cloud. Set AirDrop to *Contacts Only* or *Receive Off* except during the transfer.
- Staff upload it to AdvancedMD from the workstation, then delete both local copies.
- Alternative: a cloud folder that **is covered by a BAA** (for example, Microsoft 365 OneDrive or SharePoint, Google Workspace, or Box under the clinic's BAA). **Don't use personal iCloud, email or text messages.**

**Fallback when downtime or the network is out:** AirPrint to the room printer, then scan the paper into AdvancedMD as usual.

### Printability in AdvancedMD
AdvancedMD stores the PDF exactly as exported, so print quality is decided entirely by the form's print stylesheet. The form already targets **two letter-size pages**. Planned improvements are in §5.

---

## 4. iPad and clinic safeguards (HIPAA Security Rule)

| Area | Action |
|---|---|
| Device management | Enroll the iPads in an MDM (for example, Jamf, Intune, Kandji or Apple Business Essentials). This allows remote wipe and pushes restrictions and the Home Screen icon. |
| Encryption and lock | Passcode required (iPad storage is encrypted once a passcode is set). Auto-Lock at 2–5 minutes. |
| Cloud leakage | Turn off iCloud Drive, iCloud Photos and iCloud Safari sync on these iPads. Turn off Safari **AutoFill** for names and contacts. |
| Screenshots | Restrict via MDM, or train staff not to take them. Screenshots go to Photos. |
| Kiosk mode | Guided Access or MDM Single App Mode during the consult. |
| Local PDFs | Keep one "SDM Export" folder under *On My iPad*. Empty it at the end of each day (add to the closing checklist). |
| Audit trail | The AdvancedMD upload is the record of truth, and AdvancedMD logs who attached what. |
| E-signatures | Drawn signatures with a witness are generally valid under ESIGN/UETA. Confirm with your malpractice carrier and state rules that an electronic SDM/consent is acceptable. |
| Paperwork | Add this workflow to the Security Risk Analysis. Train staff with a one-page SOP. Keep the BAA with AdvancedMD, and with any cloud folder used in Option B, on file. |

---

## 5. Proposed changes to the form (not made yet; pending your approval)

These are small, self-contained changes to support the workflow above. The form's clinical content and behavior stay the same.

**Privacy / wipe**
1. Add a **New Patient / Clear Form** button. The form also wipes itself automatically after export, after N minutes idle, and when the tab is hidden or closed (`pagehide`). This covers the iOS tab-restore and back-forward cache.
2. Add `autocomplete="off"` on patient fields so Safari doesn't remember patient names.
3. Add a strict Content-Security-Policy `<meta>` tag that blocks all outbound connections, as technical proof of the zero-transmission behavior.

**Export / EHR**
4. Set the PDF filename automatically (Safari uses the page title), for example `SDM_Lastname-Firstname_2026-09-30.pdf`. This makes filing in AdvancedMD quick and less error-prone.
5. Add a **DOB** and/or **MRN / AdvancedMD chart #** field. Two patient identifiers help staff attach the PDF to the right chart.
6. Put a printed **header or footer on every page**: patient name, DOB, date and "Page X of 2". This is a medical-records best practice, so a separated page can still be identified.

**Correctness / print**
7. **Bug:** the default date is set from `toISOString()`, which is UTC. After about 5 pm Pacific (or 8 pm Eastern), the form fills in **tomorrow's date**. The fix is to use the iPad's local date.
8. Check that the ✏️ Draw annotation layer lines up correctly on the printed PDF. It's an absolutely-positioned full-page canvas and may shift between screen and paper layout. Either fix it or hide it in print.
9. Test black-and-white printing (initial boxes and the brand blue) so a monochrome print from AdvancedMD stays readable.

**Offline packaging (for §2.1, option 1 or 2)**
10. Add a web app manifest, an icon and a service worker so the form installs to the Home Screen and runs with no network.

---

## 6. Rollout checklist

1. ☐ Decide the delivery option (§2.1) and the export path (§3, A or B).
2. ☐ Approve the §5 form changes, plus your own content edits.
3. ☐ Configure the iPads (§4) via MDM.
4. ☐ Confirm with AdvancedMD: the document category and upload path from the iPad browser.
5. ☐ Dry run with a test patient: fill → export → upload → print from AdvancedMD → check both pages.
6. ☐ Write a one-page staff SOP and update the Security Risk Analysis.
7. ☐ Go live in one room, then expand.
