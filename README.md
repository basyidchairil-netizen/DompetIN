<div align="center">

# DompetIN
### Personal Finance Manager

*"Move beyond 'it works on my laptop.' Make it reproducible for anyone."*

<br/>

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![Gemini AI](https://img.shields.io/badge/Gemini_AI-Powered-8E75B2?style=for-the-badge&logo=google&logoColor=white)](https://aistudio.google.com)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

<br/>

> A web-based personal finance tracker with income/expense tracking, budget planning,
> saving goals, and **AI-powered financial advice** via Google Gemini — now fully containerized with Docker.

<br/>

[Quick Start](#-quick-start) · [Docker Guide](#-docker-setup) · [Verify](#-verify-the-app-works) · [🔧 Troubleshoot](#-troubleshooting) · [Team](#-team)

---

</div>

## Features

<table>
<tr>
<td width="50%">

**Dashboard Analytics**
Real-time overview of your financial health with income vs expense breakdown and monthly summaries.

**Income & Expense Tracking**
Log transactions by category and date with notes and full history view.

**Budget Planning**
Set monthly budgets per category with visual progress bars and overspend alerts.

</td>
<td width="50%">

**Saving Goals**
Create and track progress toward financial goals with deadline tracking.

**AI Financial Advice**
Chat with Google Gemini AI for personalized, context-aware money tips.

**User Profile**
Personalize your account and manage settings.

</td>
</tr>
</table>

---

## Project Info

| Item | Detail |
|---|---|
| **Project Name** | DompetIN — Personal Finance Manager |
| **Stack** | Python 3.11, Flask 3.0, SQLite, Gunicorn, Gemini AI |
| **Branch** | `chores/dockerize-project` |
| **Image Tag** | `dompetindevops/dompetin:week6` |
| **App Port** | `5000` |
| **Assignment** | Week 6 — IS Agile Project Management with DevOps |
| **Class** | IS 2026 · Eka Parima Saragih, S.Kom., M.Kom. |

---

## Prerequisites

Make sure these are installed and running before you begin:

| Tool | Minimum Version | Check |
|---|---|---|
| Docker Desktop | 24.x | `docker version` |
| Git | Any | `git --version` |

> **Tested on:** Docker 27.x · Windows 11 · MacOS

---

## Quick Start

```bash
# 1. Clone and enter the repo
git clone https://github.com/basyidchairil-netizen/DompetIN.git
cd DompetIN
git checkout chores/dockerize-project

# 2. Set up environment variables
cp .env.example .env

# 3. Build the Docker image
docker build -t dompetindevops/dompetin:week6 .

# 4. Run the container
docker run -d 
  --name dompetin-app 
  -p 5000:5000 
  --env-file .env 
  -v dompetin-data:/app/data =
  dompetindevops/dompetin:week6

# 5. Open in your browser
    http://localhost:5000
```

---

## Docker Setup

<details>
<summary><b>Step 1 — Runtime Analysis</b></summary>

<br/>

| Question | Answer |
|---|---|
| **Base runtime** | Python 3.11 |
| **Dependencies** | `requirements.txt` → `pip install -r requirements.txt` |
| **Build step** | None (interpreted language) |
| **Start command** | `gunicorn --workers 2 --bind 0.0.0.0:5000 app:app` |
| **Container port** | `5000` |
| **Config** | `GEMINI_API_KEY`, `OPENAI_API_KEY` via `.env` |
| **Data dependency** | SQLite — file-based, persisted via Docker volume |
| **Health check** | `GET http://localhost:5000/` |

</details>

<details>
<summary><b>Step 2 — Build the Image</b></summary>

<br/>

```bash
docker build -t dompetindevops/dompetin:week6 .
```

Verify the image exists:

```bash
docker image ls dompetindevops/dompetin:week6
```

Expected output:
```
REPOSITORY                TAG       IMAGE ID       CREATED         SIZE
dompetindevops/dompetin   week6     2b3cdf7a061d   X minutes ago   539MB
```

</details>

<details>
<summary><b>Step 3 — Run the Container</b></summary>

<br/>

```bash
docker run -d \
  --name dompetin-app \
  -p 5000:5000 \
  --env-file .env \
  -v dompetin-data:/app/data \
  dompetindevops/dompetin:week6
```

| Flag | Purpose |
|---|---|
| `-d` | Run in background (detached mode) |
| `--name dompetin-app` | Assign a memorable container name |
| `-p 5000:5000` | Map host port 5000 → container port 5000 |
| `--env-file .env` | Inject API keys from your local `.env` file |
| `-v dompetin-data:/app/data` | Persist SQLite database to a named volume |

App is live at **http://localhost:5000**

</details>

<details>
<summary><b>Step 4 — Environment Variables</b></summary>

<br/>

```bash
cp .env.example .env
```

Then edit `.env` with your actual keys:

```env
# Required — get yours free at: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Optional — app works without this
OPENAI_API_KEY=your_openai_api_key_here
```

| Variable | Required | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Powers the AI financial advice chatbot |
| `OPENAI_API_KEY` | Optional | Alternative AI provider (graceful fallback) |

> **Never commit your `.env` file.** It is listed in `.gitignore` for your safety.

</details>

---

## Verify the App Works

Run these checks after starting the container:

### V-01 — Container is Running

```bash
docker ps --filter "name=dompetin-app"
```

Expected: Status shows `Up ... (healthy)`

### V-02 — App Responds

```bash
# Linux / macOS
curl -o /dev/null -s -w "%{http_code}" http://localhost:5000/

# Windows PowerShell
(Invoke-WebRequest -Uri http://localhost:5000/ -UseBasicParsing).StatusCode
```

Expected: `200`

### V-03 — Core Feature Works

1. Open **http://localhost:5000** in your browser
2. Log in (a default user is seeded automatically)
3. Navigate to **Income Tracking**
4. Add a new transaction (e.g., category: Food, amount: 50000)
5. Expected: Transaction appears in the list and dashboard updates

### V-04 — Data Persists After Restart *(optional)*

```bash
docker restart dompetin-app
# Wait ~10 seconds, then reload http://localhost:5000
# Your transactions should still be there
```

---

## Logs & Status

```bash
# View recent logs
docker logs dompetin-app

# Follow logs in real time (Ctrl+C to stop)
docker logs -f dompetin-app

# Inspect full container configuration
docker inspect dompetin-app

# Open a shell inside the running container
docker exec -it dompetin-app sh

# Check environment variables inside the container
docker exec -it dompetin-app env | grep API_KEY
```

---

## Stop & Clean Up

```bash
# Stop the container
docker stop dompetin-app

# Remove the container
docker rm dompetin-app

# (Optional) Remove the image
docker rmi dompetindevops/dompetin:week6

# WARNING: This permanently deletes all saved data!
docker volume rm dompetin-data
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Port 5000 already in use | Another process is on port 5000 | Use `-p 5001:5000` instead |
| Container exits immediately | Bad `.env` or missing CMD | Run `docker logs dompetin-app` to read the error |
| Browser can't connect | Wrong port mapping | Confirm `-p 5000:5000` is in your run command |
| AI advice feature broken | `GEMINI_API_KEY` not loaded | Check `.env` exists; verify with `docker exec -it dompetin-app env` |
| Data disappears on restart | Volume not mounted | Make sure `-v dompetin-data:/app/data` flag is present |
| Build fails mid-download | Transient network error | Re-run `docker build` — cached layers will resume |
| Permission error on DB | Volume ownership issue | Run `docker exec dompetin-app chmod 777 /app/data` |

<details>
<summary><b>🩺 Full Diagnostic Cheatsheet</b></summary>

<br/>

```bash
# List all containers (including stopped)
docker ps -a

# Read container crash logs
docker logs dompetin-app

# Check the named volume exists
docker volume ls | grep dompetin

# Inspect port bindings
docker inspect dompetin-app --format '{{json .NetworkSettings.Ports}}'

# Check image layers and size
docker history dompetindevops/dompetin:week6
```

</details>

---

## Project Structure

```
DompetIN/
├── Dockerfile           ← Docker image definition
├── .dockerignore        ← Excludes secrets, cache, DBs from build
├── .env.example         ← Copy to .env and add your API keys
├── .gitignore           ← Excludes .env, __pycache__, DBs from git
│
├── app.py               ← Main Flask application (1039 lines)
├── db.py                ← Database helper & schema init
├── requirements.txt     ← Python dependencies
│
├── index.html           ← Dashboard / home page
├── login.html           ← Authentication page
├── analysis.html        ← Financial analysis view
├── budgetplaning.html   ← Budget management
├── incomeTracking.html  ← Transaction log
├── smart_saving.html    ← Saving goals
├── profile.html         ← User profile
│
├──  static/              ← CSS, JS, images
└──  README.md            ← You are here
```

---

## Team

<table>
<tr>
<td align="center" width="33%">

**Chairil Basyid**
<br/>
Student ID: 012202500058
<br/>
<sub>Contribution: —</sub>

</td>
<td align="center" width="33%">

**Syahrul Ramadhan**
<br/>
Student ID: 012202500096
<br/>
<sub>Contribution: —</sub>

</td>
<td align="center" width="33%">

**Farel Agnansyah**
<br/>
Student ID: 012202500104
<br/>
<sub>Contribution: —</sub>

</td>
</tr>
</table>

---

<div align="center">

**Week 6 Assignment — Information Systems Agile Project Management with DevOps**
<br/>
Class IS 2026 · Lecturer: Eka Parima Saragih, S.Kom., M.Kom.

<br/>


</div>
