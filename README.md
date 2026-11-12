# Render Browser

A small, isolated browser desktop that can be deployed as a Render **Docker Web Service**.
It exposes Chromium through noVNC; it does not expose a shell or terminal in the web UI.

## Security first

- Set `BROWSER_USER` and a long, unique `BROWSER_PASSWORD` in Render Environment.
- Never commit passwords, cookies, browser profiles, or Replit credentials.
- The web UI is protected by HTTP Basic Authentication. Use a unique password and keep the service URL private.
- The browser can access accounts you sign into. Sign out when finished and do not use this as a shared/public browser.
- The browser profile is ephemeral unless a Render Persistent Disk is mounted at `/data`. A restart without a disk may sign you out.
- Do not use periodic pings or scripted browser activity to defeat another provider's idle/session limits. A Render health check only reports service health; it does not guarantee a Replit workspace stays active.

## Deploy to Render

1. Push this repository to GitHub.
2. In Render choose **New + → Web Service**, connect this repository, and choose **Docker** as the runtime.
3. Set these environment variables:
   - `BROWSER_USER`: a username you choose.
   - `BROWSER_PASSWORD`: a long, unique password (do not reuse your Replit password).
   - `TZ`: `Asia/Baku` (optional).
4. Set the service's HTTP port to `10000` if Render asks for a port. The container listens on `10000`.
5. For a persistent browser profile, attach a Render Persistent Disk mounted at `/data`. Persistent disks may require a paid plan.
6. Deploy, open the Render URL, and authenticate with the browser credentials.

The noVNC desktop opens Chromium. Navigate to Replit manually and sign in directly there. Never send account passwords or session cookies in chat.


## Native Linux desktop app

You can use the AI without opening a browser window. The native Tkinter desktop app starts and manages the local `llama serve` process, provides chat, and includes API base URL / model ID / API key settings. It uses only Python's standard library plus Tkinter.

```bash
bash install-desktop.sh
```

Then launch **Render Browser Local AI** from your desktop application menu. Or run `bash run-desktop.sh` from the repository folder. If Tkinter is missing, install your Linux distribution's `python3-tk` package. The first model download needs internet; once cached, local chat can run offline. The API key is kept in memory only and is not saved.

## Optional offline AI

See [OFFLINE_AI.md](OFFLINE_AI.md) for the optional model service and deployment steps. `render-ai.yaml` is a separate, opt-in Blueprint that creates a paid private service and persistent disk; review its costs before applying. The browser-to-AI proxy/chat page is not implemented yet. Do not add model weights or secrets to Git.

## Local test

```bash
docker build -t render-browser .
docker run --rm -p 10000:10000 \
  -e BROWSER_USER=browser \
  -e BROWSER_PASSWORD='use-a-long-local-only-password' \
  render-browser
```

Open http://localhost:10000.

## Limitations

- This is a remote browser, not a guarantee of continuous Replit workspace execution.
- Render Free services may sleep when idle; paid service options and persistent disks have separate costs.
- Browser session persistence depends on a mounted persistent disk.
- No automatic login, keep-alive clicks, or background activity simulation is included.
