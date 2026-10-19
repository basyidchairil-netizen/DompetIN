# 💰 DompetIN — Personal Finance Manager

> A web-based personal finance tracker built with **Flask** and **SQLite**, featuring income/expense tracking, budget planning, saving goals, and AI-powered financial advice via Google Gemini.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)](https://flask.palletsprojects.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://docker.com)

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start with Docker](#quick-start-with-docker)
4. [Environment Variables](#environment-variables)
5. [Build the Image](#build-the-image)
6. [Run the Container](#run-the-container)
7. [Verify the App Works](#verify-the-app-works)
8. [View Logs & Status](#view-logs--status)
9. [Stop & Clean Up](#stop--clean-up)
10. [Troubleshooting](#troubleshooting)

---

## 📖 Project Overview

**DompetIN** is a personal finance management web application that helps users track their income and expenses, set budgets per category, manage saving goals, and get AI-powered financial insights.

### Core Features
- ✅ **Income & Expense Tracking** — Log transactions by category and date
- ✅ **Budget Planning** — Set monthly budgets per category with visual progress
- ✅ **Saving Goals** — Create and track progress toward financial goals
- ✅ **AI Financial Advice** — Chat with Google Gemini for personalized money tips
- ✅ **Dashboard Analytics** — Visual overview of your financial health

---

## ✅ Prerequisites

Make sure the following are installed on your system:

| Tool | Version | Check Command |
|---|---|---|
| Docker Desktop | ≥ 24.x | `docker version` |
| Git | Any | `git --version` |

> **Docker version tested:** `Docker 27.x` on Windows 11 / Ubuntu 22.04

---

## 🚀 Quick Start with Docker

```bash
# 1. Clone the repository
git clone https://github.com/<your-org>/dompetindevops.git
cd dompetindevops

# 2. Switch to the Docker branch
git checkout chores/dockerize-project

# 3. Set up environment variables
cp .env.example .env
# Then edit .env and fill in your GEMINI_API_KEY

# 4. Build the image
docker build -t dompetindevops/dompetin:week6 .

# 5. Run the container
docker run -d \
  --name dompetin-app \
  -p 5000:5000 \
  --env-file .env \
  -v dompetin-data:/app/data \
  dompetindevops/dompetin:week6

# 6. Open in browser
# → http://localhost:5000
```

---

## 🔐 Environment Variables

Copy `.env.example` to `.env` and fill in your real values:

```bash
cp .env.example .env
```

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini API key for AI advice feature |
| `OPENAI_API_KEY` | ❌ Optional | OpenAI key (app works without it) |

**`.env.example` contents:**
```env
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

> ⚠️ **Never commit your `.env` file!** It is already listed in `.gitignore`.  
> Get a free Gemini API key at: https://aistudio.google.com/app/apikey

---

## 🔨 Build the Image

```bash
docker build -t dompetindevops/dompetin:week6 .
```

Verify the image was created:

```bash
docker image ls | grep dompetin
```

Expected output:
```
dompetindevops/dompetin   week6   <image-id>   <time>   <size>
```

---

## ▶️ Run the Container

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
| `-d` | Run in background (detached) |
| `--name dompetin-app` | Give the container a memorable name |
| `-p 5000:5000` | Map host port 5000 → container port 5000 |
| `--env-file .env` | Pass API keys from your local `.env` file |
| `-v dompetin-data:/app/data` | Persist SQLite database across container restarts |

Access the app at: **http://localhost:5000**

---

## ✔️ Verify the App Works

### V-01 — Container is running
```bash
docker ps
```
Expected: `dompetin-app` shows status `Up`

### V-02 — Health check / login page loads
Open **http://localhost:5000** in your browser.  
Expected: Login page loads with DompetIN branding.

### V-03 — Core feature: Add a transaction
1. Log in (default user is seeded automatically)
2. Navigate to **Income Tracking**
3. Add a new income entry (e.g., category: Food, amount: 50000)
4. Expected: Transaction appears in the list and dashboard updates

### V-04 — Restart persistence check (optional)
```bash
docker restart dompetin-app
# Wait ~10 seconds, then open http://localhost:5000
# Your transactions should still be there (stored in the volume)
```

---

## 📊 View Logs & Status

```bash
# View recent logs
docker logs dompetin-app

# Follow logs in real time
docker logs -f dompetin-app

# Inspect container configuration
docker inspect dompetin-app

# Open a shell inside the container (for debugging)
docker exec -it dompetin-app sh
```

---

## 🛑 Stop & Clean Up

```bash
# Stop the running container
docker stop dompetin-app

# Remove the container
docker rm dompetin-app

# (Optional) Remove the image
docker rmi dompetindevops/dompetin:week6

# (Optional) Remove the data volume — WARNING: deletes all saved data!
docker volume rm dompetin-data
```

---

## 🔧 Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Port 5000 already in use | Another app is using port 5000 | Change host port: `-p 5001:5000` |
| Container exits immediately | Missing `.env` or wrong command | Run `docker logs dompetin-app` to see the error |
| Browser can't connect | Port mapping issue | Confirm `-p 5000:5000` flag was used; check `docker ps` |
| AI advice not working | `GEMINI_API_KEY` not set | Check `.env` file has the key; verify with `docker exec -it dompetin-app env` |
| Data lost after restart | No volume mounted | Ensure `-v dompetin-data:/app/data` flag is present |
| Build fails on packages | Network issue during pip | Retry `docker build` — transient network errors are common |

### Useful Diagnostic Commands

```bash
# Check all containers (including stopped ones)
docker ps -a

# Read the crash logs
docker logs dompetin-app

# Verify environment variables are loaded inside the container
docker exec -it dompetin-app env | grep API_KEY

# Check volume exists
docker volume ls | grep dompetin
```

---

## 📁 Project Structure

```
dompetindevops/
├── app.py              # Main Flask application
├── db.py               # Database helper functions
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker image definition
├── .dockerignore       # Files excluded from Docker build
├── .env.example        # Template for environment variables
├── .gitignore          # Files excluded from Git
├── static/             # CSS, JS, images
├── *.html              # Jinja2 HTML templates (login, dashboard, etc.)
└── README.md           # This file
```

---

## 👥 Team & Contributions

| Member | Student ID | Contribution |
|---|---|---|
| (Member 1) | — | — |
| (Member 2) | — | — |
| (Member 3) | — | — |

---

*Assignment: Week 6 — Information Systems Agile Project Management with DevOps*  
*Class: IS 2026 | Lecturer: Eka Parima Saragih, S.Kom., M.Kom.*
