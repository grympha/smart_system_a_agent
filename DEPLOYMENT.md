# Deployment Guide

This project is ready to deploy as a Python web service on Render.

## Prepare GitHub

From the project folder:

```bash
git init
git checkout -b codex/render-deployment
git add .
git commit -m "Prepare Smart System A web deployment"
```

Create a new empty GitHub repository, then connect it:

```bash
git remote add origin https://github.com/YOUR_USERNAME/smart_system_a_agent.git
git push -u origin codex/render-deployment
```

Open a pull request into `main`, or make this branch the default branch if this is a new repository.

## Deploy On Render

1. Sign in to Render.
2. Choose **New**.
3. Choose **Web Service**.
4. Connect the GitHub repository.
5. Select the branch to deploy.
6. Use these settings:

```text
Name: smart-system-a-agent
Runtime: Python
Build Command: pip install -r requirements.txt
Start Command: gunicorn web_app:app
```

If Render detects `render.yaml`, it can prefill these settings automatically.

## Verify After Deploy

Open the Render URL and confirm the page shows:

```text
Smart System A Agent
Analyze SSA Setup
```

Upload valid H4 and H1 CSV files to run the same strict SSA analysis used by the CLI and tests.

## Notes

- The app does not place trades.
- No broker credentials are required.
- Uploaded CSV files are analyzed in memory by the Flask request and are not stored by the app.
- If volume data is missing, condition 6 fails unless volume override is explicitly enabled.
