# Clinic Macros: start here

Everything to set up, and the prompts to give Claude Code, in order.

## A. Fix the folder

Your folder now has a subfolder whose name is literally `Clinic Macros/heidi-session/` (the slashes are part of the name). Fix that and set up this layout:

```
Clinic Macros/
  CLAUDE.md                       yours (add the text in B)
  START_HERE.md                   this file
  TESTING.md                      the shared test system for all macros
  Clinic Macros Macros.kmmacros   your export (never changed)
  heidi-session/                  ← rename the odd folder to just "heidi-session"
    EDITS.md  FEATURES.md
  heidi-to-doc/                   ← new folder
    FIXES.md
  aai-upload/                     ← new folder
    FIXES.md
```

1. Rename the folder `Clinic Macros/heidi-session/` to **`heidi-session`**.
2. Make the two new folders: `heidi-to-doc` and `aai-upload`.
3. Download from GitHub (`docs/clinic-macros/` on the branch `claude/beautiful-newton-8peto1`):
   - `START_HERE.md` and `TESTING.md` → `Clinic Macros/`
   - `heidi-session/EDITS.md` and `heidi-session/FEATURES.md` → `heidi-session/` (replace the copies there; they've been updated)
   - `heidi-to-doc/FIXES.md` → `heidi-to-doc/`
   - `aai-upload/FIXES.md` → `aai-upload/`

Claude Code builds the rest: `testkit/`, `_template/`, each `macro.applescript`, `test.conf` and `lint.extra`.

## B. Add to your `CLAUDE.md`

1. In "Current state", change `macros.kmmacros` to **`Clinic Macros Macros.kmmacros`**.
2. Under "Green zones", add:
   ```markdown
   ### Approved exception: ~/AAI
   The ~/AAI folder on the clinic Mac holds AAI note PDFs on purpose. The clinic uses them for other work.
   - Never delete, move or rename anything in ~/AAI, and never change a macro so it does.
   - The AAI macro may keep saving PDFs there.
   - It is the only place outside the green zones where patient files may stay.
   ```
3. At the end, add:
   ```markdown
   ## Testing and the macro contract
   Before writing, changing or testing any macro, read TESTING.md. Every macro, existing and new, must follow
   the macro contract in TESTING.md §3 and pass the test loop in TESTING.md §8 before it's used on real patients.
   Each macro lives in its own folder. Read that folder's EDITS.md, FIXES.md or FEATURES.md before changing it.
   ```

## C. One-time setup on the Mac (you)

1. **Clean up:**
   - Delete old `* chart.pdf` files in Downloads, then empty the Trash.
   - Delete `~/Library/Logs/Heidi macro log.txt`.
   - Clear Keyboard Maestro's clipboard history, and exclude Chrome from it.
2. **Fake patients** (`TESTING.md` §10):
   - Test A in AdvancedMD, with appointments for Dr. Hey and for the PA.
   - Test A in Heidi, with a session that has a short fake note.
   - A fake AAI Google Doc for Test A.
   - Test N in AdvancedMD only.
3. **Permissions:**
   - Accessibility and Automation for the app Claude Code runs in.
   - Chrome's "Allow JavaScript from Apple Events".
4. **Protect `~/AAI`:** FileVault on, Time Machine backup encrypted, and the folder not synced to iCloud.

## D. Prompts for Claude Code, in order

Open Claude Code in `Clinic Macros`. Wait for each prompt to finish before the next.

**1. Set up the folders and the shared test system**
```
Read CLAUDE.md, START_HERE.md and TESTING.md.
1. From "Clinic Macros Macros.kmmacros", copy each macro's AppleScript text, unchanged, into its folder as macro.applescript:
   "W add Heidi Session27" → heidi-session/, "W HEIDI to Google Doc" → heidi-to-doc/,
   "W AAI Doc to PDF, Gmail, AdvancedMD upload" → aai-upload/. Don't change the export file.
   Set up git, commit, and tag each as <folder>-original.
2. Build testkit/ (TESTING.md §5–§7), _template/ (§9), .gitignore, and .claude/commands/verify-macro.md (§8).
3. Write each macro's test.conf and lint.extra from its EDITS.md or FIXES.md.
4. Run "testkit/cycle.sh all static". The originals SHOULD fail the contract. Show me the results in plain language.
Don't change any macro.applescript yet, and don't do live runs.
```
Then fill in `testkit/config.local.sh` with the fake patients.

**2. Prove the leak checker catches real leaks.** Run the **original** Heidi macro (⌘3) yourself on Test A, then:
```
Run testkit/leakcheck.sh heidi-session for the run I just did. It must FAIL L1 and L4.
If it doesn't, the checker is broken: fix it and tell me what was wrong.
```
Do the same with the original ⌘1 on Test A's Heidi session. It must FAIL L4.

**3. Fix the Heidi session macro (v20)**
```
Do heidi-session/EDITS.md exactly as written, in order. If any "find" text isn't found exactly, stop and tell me which one.
Then run "testkit/cycle.sh heidi-session static" and fix until it passes. Commit as "heidi-session v20".
```

**4. Fix the other two macros**
```
Do heidi-to-doc/FIXES.md, then aai-upload/FIXES.md. For aai-upload edit 5 (deleting the Downloads copy if it stops
before step 4), explain it to me and wait for my OK first. Run "testkit/cycle.sh all static" until all three pass.
Then give me the data-flow check for all three macros in plain language: what each reads, moves, stores and
leaves behind. Save it as DATAFLOW.md in each folder.
```

**5. Make the new export**
```
Make macros-fixed-v1.kmmacros: a copy of the original export where each of the three macros' Execute AppleScript
action runs its folder's macro.applescript file instead of pasted text. Explain in plain language how I import it
and turn off the old macros.
```
Then import it in Keyboard Maestro and turn off the old three.

**6. Run the test loop on all three.** Set up as each `test.conf` says (Test A's appointment in AdvancedMD, Test A's Heidi session, Test A's AAI Doc). Step away from the Mac, then:
```
live OK
/verify-macro all
```
When it stops, do the person cases it lists. Those are `N` and `K` for the Heidi macro and `U` for the AAI macro.

**7. Heidi feature work: diagnostics first**
```
live OK
Read heidi-session/FEATURES.md §1. Add the --diag mode and run D1–D4 on Test A. Leak-check each diag file.
Show me the four diag reports and stop.
```
Then answer its three questions:
1. Which note names count as a Hey/PA clinic note, an AAI note or an Op note.
2. Whether Chart Print shows the newest pages first or last.
3. Whether AdvancedMD may overwrite Heidi demographics when they differ.

**8. Heidi features, one version at a time**
```
live OK
Do heidi-session/FEATURES.md v21. Add its cases to heidi-session/test.conf, then /verify-macro heidi-session until it
passes or stops. Then v22, then v23. Stop after each version and give me the summary before starting the next.
```

**9. Any new macro, any time**
```
Read TESTING.md §9. Create a new macro "<short-name>" that <what it should do>, starting from _template/.
Use fake data only. Then /verify-macro <short-name>, write its DATAFLOW.md, and add it to a new export file.
```

## E. Later

The every-morning automatic Heidi run is in `heidi-session/FEATURES.md` §6. It waits until v21–v23 work and you approve Playwright.
