# Shared Decision Making Form: Clinic Integration Plan

**Goal:** In surgery consults, the surgeon goes through the Shared Decision Making (SDM) form with the patient on an exam-room iPad. The completed form goes into the patient's chart in AdvancedMD as a PDF that prints cleanly on letter paper. Patient data is never stored or sent anywhere except the EHR.

**Decisions (approved):** an offline web app on each iPad, and AirDrop of the PDF to a front-desk Mac for upload to AdvancedMD.

| File | Purpose |
|---|---|
| `app/index.html` | The form (v14). |
| `app/sw.js`, `app/manifest.webmanifest`, icons | Make the form install to the Home Screen and run with no network. |
| `docs/IPAD_SETUP.md` | One-time setup for each iPad, and how updates reach all iPads. |
| `docs/STAFF_SOP.md` | One-page workflow for the surgeon and staff. |

---

## 1. Why this is safe

The form keeps everything **in the open page's memory only**:

- **No storage:** no `localStorage`, cookies, database or files written by the form.
- **No transmission:** there is no server, upload or form submission. A **Content-Security-Policy** in the page also tells the browser to *refuse* any outbound connection, so even an accidental future code change could not send data.
- **Wiped after every visit:** the form clears when you tap *New Patient*, after the PDF is saved, after 20 minutes idle (with a 60-second warning), and when the page is closed.
- **The only copy of PHI is the PDF.** It's saved under *On My iPad*, AirDropped peer-to-peer (encrypted, no cloud) to the front-desk Mac, uploaded to AdvancedMD (covered by the clinic's BAA), and then deleted from both devices.

The website that hosts the form only serves the **blank template**, the same way an app store serves an app. It never receives anything typed into the form.

HIPAA compliance belongs to the clinic as a whole (risk analysis, policies, training, BAAs). Record this workflow in the Security Risk Analysis. §3 lists the device safeguards.

---

## 2. Data flow

```
 Exam-room iPad (passcode, MDM, iCloud off)
   SDM form (offline, in-memory only)
     │ Save PDF → "These items were left blank — continue?" (never blocks)
     ▼
   Form builds the PDF itself (no web address / print stamps) → Share PDF… → AirDrop
     │                       PDF name: SDM_Lastname-Firstname_YYYY-MM-DD.pdf
     │ AirDrop (encrypted, peer-to-peer)
     ▼
 Front-desk Mac → upload to AdvancedMD patient chart (match by name + DOB + chart #)
     │
     ▼
 Delete the PDF on the Mac and the iPad · tap "New Patient" on the iPad
```

---

## 3. iPad and clinic safeguards

| Area | Action |
|---|---|
| Device management | Enroll the iPads in an MDM (e.g. Jamf, Intune, Kandji or Apple Business Essentials). This allows remote wipe and lets you push the restrictions below plus the form's Home Screen icon to every iPad at once. |
| Lock | Passcode required (it also turns on storage encryption). Auto-Lock at 2–5 minutes. |
| Cloud | Turn off iCloud Drive, iCloud Photos and Safari iCloud sync. Turn off Safari AutoFill (Contact Info). |
| Screenshots | Restrict via MDM, or train staff not to take them. |
| AirDrop | Set to **Contacts Only**, or **Everyone for 10 Minutes** only while sending. Give each iPad a clear name (Settings › General › About › Name), e.g. "Exam 3 iPad", so the Mac sees which room sent it. |
| Kiosk | Optional: Guided Access during the patient's part of the consult. |
| Local files | Empty *On My iPad › SDM Export* on the iPads and the Mac's Downloads folder at closing each day. |
| E-signatures | Confirm with your malpractice carrier and state rules that an electronic SDM with a drawn signature and witness is acceptable. |

---

## 4. Changes made in v14

**Content (your edits)**
- Removed the legal paragraph above the demographics.
- "Hardware" → "implant" ("Bone/Implant Problems", "implant loosening/failure", "placing of the implant", add-on "Removal of prior implants").
- Infection: added "The risk of this occurring is 1% - 2%."
- Renamed the nerve risk to **"New Neurologic Deficit (Nerve Root Irritation, Injury, or Paralysis)"** and added "The risk of this occurring is less than 1%."
- Demographics: added **Family / friends present**.
- Estimated time is always reported in hours: "4" → "4 hours", "4 S, 5.5 T" → "4 hours S, 5.5 hours T".
- **Initial all** buttons under each initials column, in every section.
- **No completion requirements.** *Print / Save PDF* lists anything blank ("These items were left blank … Continue?") and lets you continue.
- **Levels keypad:** large keys for C, T, L, Iliac Wing, 0–9, /, space and –, plus ⌫, Done and **ABC keyboard** (switches to the normal iPad keyboard). It's used for the main Levels box and for every add-on Levels box.

**Workflow and privacy**
- **Date of birth** and **Chart #** fields, so the PDF is filed to the right chart.
- Auto-clear (New Patient button, after the PDF, 20-minute idle, page close). Autofill and autocorrect are off on patient fields.
- Content-Security-Policy that blocks all outbound connections.
- PDF filename set automatically (`SDM_Lastname-Firstname_YYYY-MM-DD`).
- Every printed page has a footer: patient name, DOB, chart #, date and form version.
- Offline install (manifest + service worker). The form version shows on screen and in print.

**Fixes**
- The date defaulted to *tomorrow* in the evening (it used UTC). It now uses the iPad's local date.
- Draw/annotate marks are no longer printed. They were positioned for the screen layout and would land on the wrong text in the PDF.
- Placeholder text and date-picker icons no longer print.

---

## 5. Remaining steps

1. ☐ Choose where to host the blank form (see `docs/IPAD_SETUP.md` §1) and publish the `app/` folder.
2. ☐ Set up each iPad (`docs/IPAD_SETUP.md` §2) and the MDM restrictions (§3 above).
3. ☐ Confirm the AdvancedMD document category for SDM forms with your AdvancedMD admin.
4. ☐ Dry run on a real iPad with a test patient: fill in → Save PDF → Share PDF → AirDrop → upload → print from AdvancedMD → check both pages.
5. ☐ Train staff with `docs/STAFF_SOP.md`, and update the Security Risk Analysis.
6. ☐ Go live in one room, then the rest.

**Open question for legal review:** the consent paragraph says "all blanks were filled in prior to my signature". Now that the form allows blanks, consider adjusting that wording, or have staff write "N/A" in fields left blank on purpose.

---

## v18: PDF built by the form

iPad Safari's print added the web address, print date and a page counter to every page, and laid the form out differently (3–4 pages). Since v18 the form draws its own two-page letter PDF on the iPad (using the open-source html2canvas and jsPDF libraries stored in `app/vendor/`, which work offline and make no network requests). The PDF has the patient footer and "Page X of 2" on every page and nothing else. It stays in memory until shared through the iPad share sheet (AirDrop / Save to Files), and is gone when the form clears.
