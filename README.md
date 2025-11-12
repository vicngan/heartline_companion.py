# Heartline Care Companion

An emotionally-intelligent care companion that blends soft check-ins with logistical health support for students, healthcare workers, night-shift angels, and anxious friends. Built with Streamlit so you can deploy quickly on the web (and later wrap it for mobile if you choose).

## ✨ MVP Feature Overview
- **Emotional check-in** – captures mood, energy, and rhythm to tailor routines without guilt.
- **Daily reflection lane** – energy slider now sits beside a quick reflection card so mood journaling never hides below the fold.
- **Appointment planner** – log upcoming visits, view gentle reminders, and keep prep notes.
- **Call script generator** – auto builds phone scripts with anxiety-aware language.
- **Symptom & note tracker** – structured log you can export as a cute PDF for your care team.
- **Shift rhythm planner** – sleep/meals/movement suggestions that flex with day, night, or mixed schedules.
- **Self-compassion cues** – soft nudges that adapt when energy dips.
- **Energy-based task buddy** – gentle suggestions + the “Today, just three” rule keep momentum without overwhelm.
- **No-shame re-entry** – welcoming screen after time away so streak guilt never shows up.
- **Soft care & feelings check** – micro self-care prompts, emotional block selector, and affirmations built for gentle friends.
- **Calendar & digest lab** – export ICS files, prep Google sync, and email a weekly pastel digest to yourself or a mentor.
- **Support circle sharing** – download a privacy-aware care packet (JSON) or queue an invite for a trusted teammate.
- **Ambient cue studio** – pick a lo-fi/matcha sound loop to use as a gentle alarm (download for offline shifts).
- **Mini self check-in expander** – a consistent keyed `st.text_area` keeps dual check-ins stable even after theme swaps.

## 🧠 Tech Stack & Skills Demonstrated
- **Python 3.11+ / Streamlit 1.33** for the reactive UI, dialogs, and custom theming via injected CSS.
- **SQLite + SQLAlchemy-lite helpers** in `db.py` to persist encrypted user data, devices, and tutorial state.
- **Security & crypto**: PBKDF2-HMAC password hashing, Fernet symmetric encryption, remember-me token rotation.
- **Pandas, Altair, Matplotlib (optional)** for the quicklook charts, energy reflections, and exports.
- **FPDF & Pillow** to render printable care packets / snapshots with custom fonts.
- **Expo + React Native shell** (see `mobile_shell/`) showing how to wrap the Streamlit instance for iOS/Android and deliver push tokens.
- **Notifications / automation** integrations: SMTP email, Expo push, ICS generation, CSV exports.

## 🆕 Recent Updates
- **Sidebar glow-up** – stacked bubble-font logo, mini profile card (avatar + name only), plus “Cosmic summary” and goal overview panels pinned above navigation.
- **Goal progress tracker** – Memory & Goals tab now collects % completion sliders for year/month/day goals; the sidebar mirrors them with progress bars so users see their momentum at a glance.
- **Energy tracker widget** – new slider + note box in the widget shelf records quick energy snapshots and keeps `latest_energy` synced with suggestion engines.
- **Profile studio refresh** – dedicated Profile page with birthday (MM/DD/YYYY), zodiac picker, fun-fact field, draggable avatar uploader, and theme/ambient selections tied to the account.
- **Tutorial & help lane** – per-account onboarding tour can be reopened via the sidebar help icon; dismissal state is stored in SQLite to avoid nagging.
- **Checklist persistence** – tasks reset logic now preserves completed history inside Memory & Goals for later reflection/exports.
- **Input aesthetics** – every text/number/date input shares a slim dark border with theme-colored focus halo for consistent vibe across themes.
- **Streamlit compatibility** – deprecated `st.experimental_rerun` replaced with `st.rerun`, and page-config moved to the top to avoid multiple-call errors.

### Screen flow
1. **Home** – soft check-in, adaptive routines, recent emotional receipts, weekly digest.
2. **Health Planner** – appointments, scripts, symptom tracker, gentle reminders.
3. **Shift Support** – rhythm-aware plan, hydration cues, tiny wins, compassion popup.

## 🚀 Getting Started
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
Visit the URL Streamlit prints (usually http://localhost:8501) to use the companion.

## 🔐 Persistence, Auth & Encryption
- Data now lives in `heartline.db` (SQLite). Set `HEARTLINE_DB_PATH` to change locations.
- Each user creates an account in-app; passwords are stored as salted PBKDF2 hashes.
- Sensitive fields (notes, providers, symptoms) are encrypted per-user using a Fernet key derived from the user’s password.
- Optional “Keep me signed in for 7 days” stores a rotating session token (encrypted key + expiry) so you aren’t logged out every time the app reloads.

> ⚠️ Forgotten passwords mean encrypted data cannot be decrypted. Ship a password-reset flow before production.

## 🔔 Notifications
- Register Expo push tokens inside the **Reminder dispatch** panel then trigger pushes via Expo’s API (set `EXPO_ACCESS_TOKEN` for authenticated calls).
- Configure email reminders with SMTP env vars:
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`
- Use the in-app toast channel for quick testing without credentials.

## ☁️ Playbook Extras (Sidebar)
- **Calendar lab** – Grab `heartline-appointments.ics` and import into Google/Outlook; the Google sync form tells you which OAuth scopes to request later.
- **Weekly digest** – Home view can email (staged) or copy a 7-day summary, plus download ready-to-attach PDF + PNG versions.
- **Support circle** – Download a JSON care packet or stage an email invite to loop in a trusted person.
- **Ambient cues** – Pick a lo-fi loop, download it, and run your alarms in airplane mode for offline shifts.
- **Energy buddy** – Surface “low / medium / glow” task ideas, no-shame re-entry, self-care cues, and affirmations right on the Home dashboard.

## 📱 Mobile Shell
A lightweight Expo WebView shell lives in `mobile_shell/`. It lets you deploy the hosted Streamlit experience to iOS/Android quickly.

```bash
cd mobile_shell
npm install
expo start
```

- Update `app.json -> extra.heartlineUrl` to your deployed Streamlit URL (ngrok for local dev, production domain for release).
- Replace placeholder icon/splash assets before shipping.
- Use `expo run:ios` / `expo run:android` for store builds; add push entitlements if you plan to reuse Expo notifications captured in Streamlit.

## 🛠 Customizing & Next Steps
- **Persistence backend swap** – wire the DB layer to Supabase/Firebase if you need multi-region sync or built-in auth resets.
- **Calendar integrations** – connect Google Calendar / iCal APIs to auto-create appointments noted inside Heartline.
- **Insights** – connect the digest + support-circle hooks to a transactional email or SMS service.
- **Design polish** – layer on a design system (shades of blush, serif fonts) via Streamlit themes or migrate UI into React Native/Flutter when ready for full mobile polish.
- **QA checklist** – after layout tweaks, run `python3 -m py_compile app.py` then `streamlit run app.py` to confirm there are no lingering NameErrors or duplicate widget IDs.

Take what resonates, leave the rest — Heartline adapts with you. 💗
