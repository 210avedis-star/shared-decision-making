# iPad Setup (multiple iPads)

The form is a small static website, the `app/` folder. Each iPad downloads it once and then runs it **offline** from the Home Screen. Patient data never goes back to the website (see `CLINIC_INTEGRATION_PLAN.md` §1).

## 1. Host the blank form (one time)

Any static host with **HTTPS** works. HTTPS is required for offline mode. Upload the **contents of `app/`** and you get one URL that every iPad uses:

| Option | Notes |
|---|---|
| GitHub Pages | Publish the `app/` folder from this repository. Free if the repository is public; a private repository needs a paid GitHub plan. |
| Netlify / Cloudflare Pages | Drag and drop the `app/` folder. Free tier is fine. |
| Clinic web server | Fine if it has a valid HTTPS certificate the iPads trust. |

The host only ever serves the empty template, so it holds no PHI and needs no BAA. Don't add analytics, chat widgets or other scripts to the hosted page.

## 2. Each iPad (about 2 minutes)

1. Open the form URL in **Safari**.
2. Tap **Share → Add to Home Screen**, name it **"SDM Form"**, then tap **Add**.
3. Open it once from the Home Screen while on Wi-Fi so it saves itself for offline use.
4. Test: turn on Airplane Mode, then open **SDM Form**. It should load normally.
5. In **Files**, create the folder **On My iPad › SDM Export**.
6. Name the iPad by room: Settings › General › About › Name, e.g. "Exam 3 iPad".
7. Apply the restrictions in `CLINIC_INTEGRATION_PLAN.md` §3: passcode, iCloud off, AutoFill off, AirDrop Contacts Only.

With an MDM, you can push steps 2 and 7 to all iPads at once: a **Web Clip** pointing at the form URL (set to open full-screen), plus a restrictions profile.

## 3. Updating the form on all iPads

1. Edit `app/index.html`. Raise `FORM_VERSION` in it, and `CACHE` in `app/sw.js` to match (e.g. `'15'` and `'sdm-form-v15'`).
2. Re-publish the `app/` folder to the host.
3. Each iPad picks up the new version the next time the form opens while online. If it's offline, it keeps using the version it last saved.
4. Check: the version appears at the bottom of the screen ("Form v15") and in every printed footer. Make sure every iPad shows the new number.

## 4. Front-desk Mac

- AirDrop: Finder › AirDrop › "Allow me to be discovered by: Contacts Only". Received files go to **Downloads**.
- After uploading to AdvancedMD, delete the PDF from Downloads **and empty the Trash**.
- The Mac should have FileVault on, a screen lock and a user login (standard HIPAA workstation controls).
