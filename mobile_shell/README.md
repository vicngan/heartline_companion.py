## Heartline Mobile Shell (Expo + WebView)

This lightweight wrapper loads the deployed Streamlit experience inside a native container so you can ship to the App Store or Play Store without rebuilding every screen twice.

### Quick start
```bash
cd mobile_shell
npm install
expo start
```

Update `extra.heartlineUrl` inside `app.json` (and optionally set the `HEARTLINE_URL` env var at build time) to point at your hosted Streamlit deployment before building release binaries.

### Branding
- Replace the placeholder icon/adaptive-icon/splash files referenced in `app.json` with your own assets (1024×1024 PNG works for both icons; 1242×2436 PNG for splash).
- Adjust colors to match Heartline’s palette.

### Native builds
- `expo run:ios` / `expo run:android` produce native projects you can open in Xcode or Android Studio for store submission.
- Add push-notification entitlements if you plan to use Expo push tokens captured in the Streamlit app.

### Local testing tips
- When running Streamlit locally, expose it via `ngrok` or `cloudflared` and set that URL in `app.json` so simulators can reach it.
- Use Expo’s `Constants.expoConfig.extra.heartlineUrl` (or `process.env.HEARTLINE_URL`) for multi-env builds (staging vs prod).
