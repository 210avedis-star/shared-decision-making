#!/usr/bin/env python3
"""Builds gas/Sdm.html, the Google (Apps Script) copy of the form, from app/index.html.

The Google copy runs inside the clinic's signed-in Brace Forms Apps Script project at
<web app URL>?app=sdm. There "Save and send" puts the PDF in the "_SDM Upload Queue" Drive folder
and the front desk Mac's upload macro files it in the AdvancedMD chart. The offline iPad app
(app/, on Netlify) is unchanged and still sends nothing.

What changes in the Google copy: no zero-network policy, no offline install (manifest / service
worker), and the PDF libraries come from the Apps Script project (getPdfMaker) instead of app/vendor.
Run: python3 tools/build_gas.py, then paste gas/Sdm.html into the project's "Sdm" HTML file."""
import pathlib, re
B = pathlib.Path(__file__).resolve().parent.parent
s = (B / 'app/index.html').read_text()

def cut(pattern, flags=0, count=1):
    global s
    s, n = re.subn(pattern, '', s, flags=flags)
    assert n == count, (pattern, n)

cut(r'<!-- Zero-transmission policy[^\n]*\n<meta http-equiv="Content-Security-Policy"[^\n]*\n')
cut(r'<link rel="manifest"[^\n]*\n')
cut(r'<link rel="apple-touch-icon"[^\n]*\n')
cut(r'<!-- PDF builders[^\n]*\n<script src="vendor/html2canvas.min.js"></script>\n<script src="vendor/jspdf.umd.min.js"></script>\n')
cut(r"/\* ---------- Offline: cache the form[^\n]*\nif\('serviceWorker' in navigator[^\n]*\n[^\n]*\n\}\n")
s, n = re.subn(r'(<div class="legal-note">).*?(<span id="versionNote">)',
               r'\1Tap “Save and send” to file the signed form in the patient’s AdvancedMD chart, then “Clear for next patient”. \2', s, count=1)
assert n == 1
s = s.replace('<head>\n', '<head>\n<base target="_top">\n', 1)
(B / 'gas/Sdm.html').write_text(s)
print('built gas/Sdm.html', (B / 'gas/Sdm.html').stat().st_size, 'bytes')
