# Task 1: HIPAA edits to the Heidi macro (v19 → v20)

## Goals

When v20 is done:

1. **Patient data exists only in AMD, in Heidi, and in memory while the macro runs.** Nothing goes to disk, the clipboard, notifications, the script file or the log.
2. **The chart PDF never touches the disk.** It goes from the AMD report tab, through memory, into Heidi.
3. **The log is safe to read and share.** It has step names, stages, counts and yes/no results. Every line passes through `redact()`.
4. **Error messages are generic.** They never contain a name, DOB, date, email or ID, because Keyboard Maestro can save them.
5. **The macro is testable without a person:** a `--test` mode, `STAGE` markers, and a final `RESULT:` line.
6. **Everything else behaves exactly as v19 does.** Don't change templates, matching rules, timing or flow except where listed here.

## Rules for making the edits

- Work on a copy: `heidi_add_session.applescript` (v19) → commit as-is first, then edit.
- The `JS_*` properties are JavaScript inside AppleScript strings. In them, `"` is written `\"` and `\` is written `\\`. The replacements below avoid both where possible. Keep the escaping exactly right.
- Each find string below is unique in v19. If one isn't found exactly, stop and report it. Don't guess.
- After the edits, `test/cycle.sh static` must pass (see `TEST_LOOP.md`).

---

## Part 1: top of the script

1. After `use scripting additions`, add:
   ```applescript
   use framework "Foundation"

   global RUNLOG, PHI_WORDS, TEST_LAST
   ```
2. Delete `property CHART_EMAIL : ""` and `property RUNLOG : ""`. *Why:* AppleScript can save property values back into the script file.

## Part 2: inside `JS_HEIDI`

| # | Find | Replace with | Why |
|---|---|---|---|
| 2.1 | `if (window.__kmH && window.__kmH.v === 19) return 'lib-ok';` | same with `20` | An open Heidi tab must load the new code. |
| 2.2 | `var H = { v: 19, gen: 0, log: [] };` | same with `20` | Same. |
| 2.3 | `log('    FAILED - snapshot follows'); log(pageMap());` | `log('    FAILED'); if (window.__kmDebug) console.log(pageMap());` | The snapshot captured other patients from the sidebar. |
| 2.4 | `log('    real typing gave ' + JSON.stringify(v) + ', falling back to page typing');` | `log('    real typing mismatch, using page typing');` | Typed value = PHI. |
| 2.5 | `log('    search results: ' + (cands.length ? cands.map(function(c){ return JSON.stringify(c.text.slice(0, 60)) + ' [' + c.why + ']'; }).join(' \| ') : 'none'));` | `log('    search results: ' + cands.length + (cands.length ? ' (' + cands.map(function(c){ return c.why; }).join(', ') + ')' : ''));` | Search results = other patients. |
| 2.6 | `log('    identifier box shows ' + JSON.stringify(inp.value) + ', retyping');` | `log('    identifier box mismatch, retyping');` | |
| 2.7 | `log('    creating patient: ' + JSON.stringify(txt(opt)));` | `log('    creating patient');` | |
| 2.8 | `log('    Create row never showed the full name; it shows ' + JSON.stringify(o2 ? txt(o2) : '(none)'));` | `log('    Create row never showed the full name');` | |
| 2.9 | `log('    asked about partial match -> ' + ans);` followed by `var idx = labels.indexOf(ans);` | `var idx = labels.indexOf(ans);` followed by `log('    partial match answer: ' + (idx >= 0 ? 'option ' + (idx + 1) : 'create new'));` | The answer label contains a name. |
| 2.10 | `if (!row) return fail('could not find \"' + want + '\" again in the search results');` | `if (!row) return fail('could not find the chosen patient again in the search results');` | |
| 2.11 | `log('    warning: header shows ' + JSON.stringify(txt(headerName(A))) + ' - first name missing');` | `log('    warning: header is missing the first name');` | |
| 2.12 | `log('    Past sessions rows: ' + labels.map(txt).join(' \| ') + ' (this session: ' + cur + ')');` | `log('    Past sessions rows: ' + labels.length);` | Dates of service. |
| 2.13 | `if (!mine) return fail('this session (' + cur + ') is not in the Past sessions list');` | `if (!mine) return fail('this session is not in the Past sessions list');` | |
| 2.14 | `if (diff === 0) { log('    calendar on ' + txt(monthHeader(cal))); return true; }` | `if (diff === 0) { log('    calendar on the right month'); return true; }` | |
| 2.15 | `log('    typed time -> ' + JSON.stringify(ti.value));` | `log('    typed time');` | |
| 2.16 | `var dd = day.closest('[data-day]'); log('    day cell ' + (dd ? dd.getAttribute('data-day') : '(no data-day)') + ' ' + desc(day));` | `log('    day cell found');` | |
| 2.17 | `return fail('picked the wrong day cell (' + dx.toDateString() + ')');` | `return fail('picked the wrong day cell');` | |
| 2.18 | `if (!ok) return fail('did not stick; date button shows ' + (dateBtn() ? txt(dateBtn()) : 'nothing'));` | `if (!ok) return fail('date did not stick');` | |
| 2.19 | `log('    ' + label + ': ' + (norm(el.value) === norm(val) ? 'filled' : 'NOT filled (box shows ' + (label === 'Email' ? (el.value ? 'something else' : 'nothing') : JSON.stringify(el.value)) + ')'));` | `log('    ' + label + ': ' + (norm(el.value) === norm(val) ? 'filled' : 'NOT filled'));` | |
| 2.20 | `else if (gOk()) log('    gender already ' + A.sex);` | `else if (gOk()) log('    gender already set');` | |
| 2.21 | `if (!opt) { log('    gender option ' + A.sex + ' not found');` | `if (!opt) { log('    gender option not found');` | |
| 2.22 | `log('    gender now ' + JSON.stringify(inputFor('Gender', true) ? txt(inputFor('Gender', true)) : ''));` | `log('    gender ' + (gOk() ? 'set' : 'NOT set'));` | |
| 2.23 | `log('    PDF bytes received: ' + Math.round(F.b64.length * 0.75));` | `log('    PDF received: ' + Math.round(F.b64.length * 0.75 / 1024) + ' KB');` | |
| 2.24 | the `if (!fi) { log('    file inputs on page: ' + … ); log(pageMap()); }` line in `H.phase2` | `if (!fi) log('    file inputs on page: ' + document.querySelectorAll('input[type=file]').length);` | |
| 2.25 | `H.log = ['=== Heidi ' + phase + ' ===', 'A=' + JSON.stringify(Object.assign({}, A, { email: A.email ? '(set)' : '' }))];` | `H.log = ['=== Heidi ' + phase + ' ===', 'provider kind=' + (A.providerKind \|\| '?') + ', email=' + (A.email ? 'yes' : 'no')];` | The whole patient record was logged. |

(`\|` in the table means a plain `|`.)

**2.26 Replace the whole `desc()` function** so it never records on-screen text:
```js
function desc(e){
  var a = [];
  ['role','type','data-state'].forEach(function(k){ var v = e.getAttribute(k); if (v) a.push(k + '=' + String(v).slice(0, 20)); });
  var r = e.getBoundingClientRect();
  return e.tagName.toLowerCase() + (a.length ? '[' + a.join(' ') + ']' : '') + ' @' + Math.round(r.left) + ',' + Math.round(r.top) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height);
}
```

**2.27 Replace the whole `startWatch()` function** (it logged the date button every 120 ms) with:
```js
function startWatch(){ return function(){}; }
```

**2.28 After the `H.getLog = …` line, add:**
```js
H.clear = function(){ H.log = []; var b = document.getElementById('km-banner'); if (b) b.remove(); return 'ok'; };
```

**2.29 Test mode never waits for a person.** At the top of `async function need(msg, buttons){`, add as the first line:
```js
  if (window.__kmTest) throw new Error('needs a person');
```
*Why:* the automated test must fail fast and say which step needed help, instead of waiting forever. `step()` adds the step name to the error.

## Part 3: the AMD and report scripts

**`JS_AMD_READ`**

- 3.1 In the `return 'ERR|~|' + (loggedOut ? …` line:
  - change `The log is on your clipboard - paste it to Claude.` to `Details are in Library/Logs/Heidi macro log.txt.`
  - change the tail `+ ' | text near DOB: ' + JSON.stringify(around) + '\\n' + docDiag();` to `+ ', DOB pattern found=' + (around ? 'yes' : 'no');`
- 3.2 Replace `return 'ERR|~|No upcoming appointment found for ' + out.identifier + ' (no \"Next:\" date in AdvancedMD).|~|appointment tabs open: ' + JSON.stringify(appts);` with `return 'ERR|~|No upcoming appointment found for the patient on screen (no Next: date in AdvancedMD).|~|appointment tabs open: ' + appts.length;`
- 3.3 In the `OPENAPPT` return, change `'appointment tabs open: ' + JSON.stringify(appts)` to `'appointment tabs open: ' + appts.length`.
- 3.4 Replace the final `return ['OK', …].join('|~|');` with:
  ```js
  return ['OK', JSON.stringify(out), out.identifier, out.date, out.time, out.fileName, 'provider=' + (out.provider || '(not read)') + ' kind=' + (out.providerKind || '?'), ids.join(','), out.last, out.first, out.dob, out.email].join('|~|');
  ```
  Items 9–12 feed `redact()`.

**`JS_AMD_OPEN_APPT`**

- 3.5 Replace `return 'clicked ' + JSON.stringify((el.textContent || '').trim().slice(0, 40));` with `return 'clicked';`.

**`JS_AMD_PRINT`**

- 3.6 Replace `if (MODE === 'url') return document.documentElement.getAttribute('data-km-report') || '';` with:
  ```js
  if (MODE === 'url') { var u = document.documentElement.getAttribute('data-km-report') || ''; if (u) document.documentElement.removeAttribute('data-km-report'); return u; }
  ```

**`JS_REPORT_PDF`**

- 3.7 Replace `window.__kmPdf.info = 'from ' + url + ' (' + buf.length + ' bytes)';` with `window.__kmPdf.info = '(' + Math.round(buf.length / 1024) + ' KB)';`.

## Part 4: AppleScript handlers

### 4.1 Replace `on run`

```applescript
on run argv
	set RUNLOG to "Heidi – Add Upcoming Session  •  " & (do shell script "date '+%Y-%m-%d %H:%M'") & linefeed
	set PHI_WORDS to {}
	set TEST_LAST to ""
	try
		if (count of argv) ≥ 2 and (item 1 of argv) is "--test" then set TEST_LAST to (item 2 of argv)
	end try
	if TEST_LAST is not "" then my addLog("TEST MODE")
	try
		my mainFlow()
		my addLog("RESULT: PASS")
		my saveLog()
		set RUNLOG to ""
		set PHI_WORDS to {}
	on error errMsg number errNum
		set safeMsg to my redact(errMsg)
		my addLog("RESULT: FAIL — " & safeMsg & " (" & errNum & ")")
		my saveLog()
		set RUNLOG to ""
		set PHI_WORDS to {}
		error safeMsg number errNum
	end try
end run
```

The `try` around `argv` matters: when the macro runs from Keyboard Maestro or Script Editor, `argv` may be empty or missing.

### 4.2 Replace `mainFlow`

Changes from v19:
- `STAGE` markers;
- a test-mode guard;
- generic log lines, errors and notifications;
- the email comes from Demographics;
- page variables are wrapped in a function;
- PDF variables are cleared after use.

```applescript
on mainFlow()
	my addLog("STAGE amd-read")
	set amdTab to my findTab("advancedmd.com", "ReportViewer")
	if amdTab is missing value then error "No AdvancedMD tab found in Chrome. Open the patient's upcoming appointment first."
	set r to my splitText(my runJS(amdTab, JS_AMD_READ), SEP)
	if (item 1 of r) is "OPENAPPT" then
		my addLog("Opening upcoming appointment from the timeline (" & (item 5 of r) & ")")
		my focusTab(amdTab)
		set js to my replaceText(my replaceText(JS_AMD_OPEN_APPT, "__MON__", item 2 of r), "__DAY__", item 3 of r)
		set clickRes to my runJS(amdTab, js)
		my addLog("Timeline click: " & clickRes)
		if clickRes is "notfound" then error "Couldn't find the upcoming appointment on the AdvancedMD timeline. Open it and run the macro again."
		repeat 30 times
			delay 0.5
			set r to my splitText(my runJS(amdTab, JS_AMD_READ), SEP)
			if (item 1 of r) is "OK" then exit repeat
		end repeat
		if (item 1 of r) is "OPENAPPT" then error "The upcoming appointment didn't open in AdvancedMD. Open it and run the macro again."
	end if
	if (item 1 of r) is not "OK" then
		set errMsg to (item 2 of r) as text
		if (count of r) > 2 then my addLog("AMD read diagnostic: " & ((item 3 of r) as text))
		error errMsg
	end if
	set amdJSON to item 2 of r
	set patientName to item 3 of r
	set apptDate to item 4 of r
	set apptTime to item 5 of r
	set pdfName to item 6 of r
	set amdIds to item 8 of r
	set PHI_WORDS to {patientName, item 9 of r, item 10 of r, item 11 of r, item 12 of r, apptDate} & my splitText(amdIds, ",")
	if TEST_LAST is not "" and (item 9 of r) is not TEST_LAST then error "TEST MODE: the patient on screen is not the test patient. Nothing was changed."
	my addLog("AMD read: ok | " & (item 7 of r))
	if apptDate is "" or apptTime is "" then
		if TEST_LAST is not "" then error "TEST MODE: appointment date/time not readable (needs a person)."
		set ans to my askText("Couldn't read the appointment date/time for " & patientName & " in AdvancedMD (is the appointment tab open?)." & return & return & "Type it as  MM/DD/YYYY h:mm AM", "")
		set p to my splitText(ans, " ")
		set apptDate to item 1 of p
		set apptTime to my joinText(items 2 thru -1 of p, " ")
		set end of PHI_WORDS to apptDate
		my addLog("Date/time typed by user")
	end if

	my addLog("STAGE amd-email")
	set emailFix to ""
	if amdJSON contains "@" then
		my addLog("Email: found on the chart")
	else
		set em to my emailFromDemographics(amdTab)
		if em contains "@" then
			set emailFix to "A.email=" & my jsq(em) & ";"
			set end of PHI_WORDS to em
			my addLog("Email: found on Demographics")
		else
			my addLog("Email: none in AdvancedMD")
		end if
	end if
	set A to "var A=" & amdJSON & ";A.date=" & my jsq(apptDate) & ";A.time=" & my jsq(apptTime) & ";A.tplHey=" & my jsq(TPL_HEY) & ";A.tplOther=" & my jsq(TPL_OTHER) & ";A.template='';" & emailFix
	set testFlag to "window.__kmTest=" & (TEST_LAST is not "") & ";"
	display notification "Setting up the Heidi session…" with title "Heidi macro"

	my addLog("STAGE heidi-phase1")
	set heidiTab to my findTab("heidihealth.com", "")
	if heidiTab is missing value then set heidiTab to my openTab(HEIDI_HOME)
	my focusTab(heidiTab)
	tell application "Google Chrome" to set hu to URL of (tab id (item 2 of heidiTab) of window id (item 1 of heidiTab))
	if hu does not contain "/scribe/session" then
		my addLog("Heidi tab was not on Scribe sessions - going there first")
		tell application "Google Chrome" to set URL of (tab id (item 2 of heidiTab) of window id (item 1 of heidiTab)) to HEIDI_HOME
		delay 1
		my waitLoaded(heidiTab)
		delay 2
	end if
	set outcome to my runPhase(heidiTab, "(function(){" & testFlag & A & "window.__kmH.start('phase1', A);})();", 240)
	if outcome is not "new" then
		my addLog("Outcome: existing patient")
		display notification "Session ready" with title "Heidi macro" subtitle "Existing patient"
		return
	end if
	my addLog("Outcome: new patient")

	my addLog("STAGE amd-chart")
	set b64 to my getChartPDF(amdTab, amdIds)

	my addLog("STAGE heidi-phase2")
	my focusTab(heidiTab)
	set F to "var F={name:" & my jsq(pdfName) & ",b64:\"" & b64 & "\"};"
	set b64 to ""
	my runPhase(heidiTab, "(function(){" & testFlag & A & F & "window.__kmH.start('phase2', A, F);})();", 180)
	set F to ""
	display notification "Session ready" with title "Heidi macro" subtitle "New patient + chart attached"
end mainFlow
```

*Why the `(function(){ … })();` wrapper:* without it, `var A` and `var F` become page globals. The whole chart would then sit in the Heidi tab's memory until it reloads.

### 4.3 Replace `getChartPDF`

Changes from v19:
- The signature is now `getChartPDF(amdTab, amdIds)`.
- Remove the Downloads copy, the `km_chart.b64` temp file, `emailFromPDF` and the manual-save fallback.
- Check the report's patient ID with `idFromURL` instead of `echo | sed`. The URL contains the patient ID.
- In test mode, the manual banner path fails right away.
- Run `window.__kmPdf = null` before closing the report tab.

```applescript
on getChartPDF(amdTab, amdIds)
	set manualMsg to "Heidi macro is waiting: open Chart Print (printer icon, right toolbar) and click Print. It continues by itself once the chart opens."
	my focusTab(amdTab)
	set existing to my reportTabIDs()
	set auto to false
	set s to my runJS(amdTab, my amdJS("open", ""))
	my addLog("AMD chart print button: " & s)
	if s is "panel" or s is "clicked" then
		repeat 30 times
			if my runJS(amdTab, my amdJS("panel", "")) is "panel" then
				set auto to true
				exit repeat
			end if
			delay 0.3
		end repeat
	end if
	if auto then
		delay 0.6
		if my runJS(amdTab, my amdJS("print", "")) is not "clicked" then set auto to false
	end if
	my addLog("AMD chart print automatic: " & auto)
	if not auto and TEST_LAST is not "" then error "TEST MODE: Chart Print could not be opened automatically (needs a person)."
	if not auto then my runJS(amdTab, my amdJS("banner", manualMsg))

	set waitSecs to 20
	if not auto then set waitSecs to 180
	set t0 to current date
	repeat
		set rep to my newReportTab(existing)
		if rep is not missing value then
			my addLog("Report tab opened")
			exit repeat
		end if
		if ((current date) - t0) > 3 then
			set u to my runJS(amdTab, my amdJS("url", ""))
			if u is not "" then
				my addLog("Report popup was blocked; opening captured URL")
				set rep to my openTab(u)
				set u to ""
				exit repeat
			end if
		end if
		if ((current date) - t0) > waitSecs then
			if auto and TEST_LAST is "" then
				set auto to false
				set waitSecs to 180
				set t0 to current date
				my runJS(amdTab, my amdJS("banner", manualMsg))
			else
				my runJS(amdTab, my amdJS("banner", ""))
				error "The Chart Print report never opened."
			end if
		end if
		delay 0.5
	end repeat
	my runJS(amdTab, my amdJS("banner", ""))

	-- SAFETY: the printed chart must belong to the patient on screen
	tell application "Google Chrome" to set repURL to URL of (tab id (item 2 of rep) of window id (item 1 of rep))
	set repId to my idFromURL(repURL)
	set repURL to ""
	set idOK to (repId is not "" and amdIds is not "" and ("," & amdIds & ",") contains ("," & repId & ","))
	my addLog("Chart report matches the patient on screen: " & idOK)
	if not idOK then
		try
			tell application "Google Chrome" to close (tab id (item 2 of rep) of window id (item 1 of rep))
		end try
		error "Stopped: the Chart Print report does not match the patient on screen. Nothing was attached. Close any open Chart Print screens in AdvancedMD and run again."
	end if

	-- PDF bytes, memory only
	my waitLoaded(rep)
	delay 1
	my runJS(rep, JS_REPORT_PDF)
	set b64 to ""
	set t0 to current date
	repeat
		delay 0.5
		set p to my splitText(my runJS(rep, "window.__kmPdf ? (window.__kmPdf.state + '|~|' + (window.__kmPdf.state === 'done' ? window.__kmPdf.data : window.__kmPdf.err)) : 'none|~|'"), SEP)
		if item 1 of p is "done" then
			set b64 to item 2 of p
			my addLog("Report PDF grabbed " & my runJS(rep, "window.__kmPdf.info"))
			exit repeat
		end if
		if item 1 of p is "error" or ((current date) - t0) > 30 then
			my addLog("Report PDF grab failed: " & (item 1 of p) & " " & (item 2 of p))
			exit repeat
		end if
	end repeat
	set p to {}
	try
		my runJS(rep, "window.__kmPdf = null;")
		tell application "Google Chrome" to close (tab id (item 2 of rep) of window id (item 1 of rep))
	end try
	if b64 is "" then error "Couldn't read the Chart Print PDF. The Heidi session is set up, but no chart was attached."
	return b64
end getChartPDF
```

### 4.4 Delete the whole `emailFromPDF` handler

### 4.5 Replace `addLog`, `saveLog` and `pullHeidiLog`

```applescript
on addLog(s)
	set RUNLOG to RUNLOG & my redact(s) & linefeed
end addLog

on saveLog()
	try
		set p to (POSIX path of (path to library folder from user domain)) & "Logs/Heidi macro log.txt"
		my writeText(p, my redact(RUNLOG)) -- second pass catches lines logged before the patient was known
	end try
end saveLog

on pullHeidiLog(tabRec)
	try
		my addLog(my runJS(tabRec, "window.__kmH ? window.__kmH.getLog() : '(no Heidi log)'"))
		my runJS(tabRec, "window.__kmH && window.__kmH.clear()")
	end try
end pullHeidiLog
```

### 4.6 Add new handlers (under `-- text helpers`)

```applescript
on redact(s)
	return my redactWith(s, PHI_WORDS)
end redact

-- Removes the given words, plus anything shaped like an email, date, ID (5+ digits) or "Last, First" name
on redactWith(s, words)
	set t to current application's NSMutableString's stringWithString:(s as text)
	set opts to (current application's NSRegularExpressionSearch) + (current application's NSCaseInsensitiveSearch)
	repeat with w in words
		set w to w as text
		if length of w > 1 then
			set pat to "\\b" & ((current application's NSRegularExpression's escapedPatternForString:w) as text) & "\\b"
			(t's replaceOccurrencesOfString:pat withString:"[phi]" options:opts range:{0, t's |length|()})
		end if
	end repeat
	set pats to {"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}", "\\b\\d{1,2}[/-]\\d{1,2}[/-]\\d{2,4}\\b", "\\b\\d{5,}\\b", "\\b[A-Z][A-Za-z'\\-]+ ?, ?[A-Z][A-Za-z'\\-]+( [A-Z]\\.?)?"}
	set reps to {"[email]", "[date]", "[id]", "[name]"}
	repeat with i from 1 to count of pats
		(t's replaceOccurrencesOfString:(item i of pats) withString:(item i of reps) options:(current application's NSRegularExpressionSearch) range:{0, t's |length|()})
	end repeat
	return t as text
end redactWith

on idFromURL(u)
	set AppleScript's text item delimiters to {"?id=", "&id="}
	set parts to text items of u
	set AppleScript's text item delimiters to ""
	if (count of parts) < 2 then return ""
	set n to ""
	repeat with c in (characters of (item -1 of parts))
		if "0123456789" does not contain (c as text) then exit repeat
		set n to n & c
	end repeat
	return n
end idFromURL

on emailFromDemographics(amdTab)
	if my runJS(amdTab, my replaceText(JS_AMD_EMAIL, "__MODE__", "click")) is not "clicked" then return ""
	repeat 10 times
		delay 0.5
		set em to my runJS(amdTab, my replaceText(JS_AMD_EMAIL, "__MODE__", "read"))
		if em contains "@" then return em
	end repeat
	return ""
end emailFromDemographics
```

## Part 5: known risk to watch in testing

`emailFromDemographics` switches AMD to the Demographics screen. If the later Chart Print step can't find its printer button there, the live test fails at `STAGE amd-chart`. Fix it by returning to the chart view before Chart Print. Don't fix it by skipping the email.

## Part 6: acceptance criteria

- `test/cycle.sh static` passes: it compiles, the forbidden-pattern lint is clean, every `JS_*` string parses, and the `redactWith` tests pass.
- `test/cycle.sh live` passes for every case in `TEST_LOOP.md`, and every leak check passes.
- The macro still works from Keyboard Maestro with no arguments (normal mode). One manual run by a person on the test patient.

