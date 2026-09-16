# OPSINTEL: Executive Operational Governance AI (POC)
**Master Documentation & Project Overview**

## 1. Project Vision
OPSINTEL is a conceptual Proof of Concept (POC) designed to provide Executive IT Leaders (CTOs, VPs of Engineering) with real-time, AI-synthesized intelligence regarding their massive IT infrastructure. Instead of digging through thousands of raw JIRA tickets, Datadog alerts, or ServiceNow incidents, OPSINTEL ingests this operational data, runs it through an advanced LLM (Google Gemini), and outputs highly polished, board-ready 15-page Executive Summaries, predictive anomaly detection, and visual SLA trend metrics.

## 2. Core Architecture
The system is built as a highly performant, decoupled microservice architecture.

### Backend (FastAPI / Python)
- **Framework:** FastAPI with Uvicorn (ASGI)
- **Database:** SQLite (SQLAlchemy ORM) storing Incidents, Problems, Changes, and SLA Records.
- **AI Engine:** Google Gemini (using both `google-genai` and `google-generativeai` SDKs with automatic fallback logic across `gemini-1.5-flash`, `gemini-1.5-pro`, and legacy models).
- **Scheduler & Background Tasks:** Custom asyncio threaded scheduler running live simulated incident injections and cron-based massive executive report generation.
- **WebSocket Gateway:** Real-time data streaming over WebSockets for live dashboard updates.

### Frontend (React / Vite / TypeScript)
- **Framework:** React 18 with Vite.
- **Styling:** TailwindCSS with modern dark-mode aesthetics, glassmorphism, and Lucide React iconography.
- **State Management:** Custom React Contexts (`AuthContext`).
- **Real-Time Layer:** Native WebSocket client connecting to the FastAPI `ws/dashboard` endpoint for live incident grid updates.

## 3. Key Components & Working Logic

### 3.1 Data Ingestion & Synthetic Generation (`generate_data.py`)
To prove the AI's capabilities, we seeded a massive synthetic dataset containing **25,000+ Incidents**, **2,900 Problems**, **5,000 Changes**, and thousands of **SLA breached records**. These simulate 6-months of operations for critical services like `SVC_PAYMENT`, `SVC_AUTH`, and `SVC_DB`. 
- Spikes and anomalies (e.g., failed deployments causing P1 outages) are intentionally injected to give the AI engine dense "root cause" signals to detect.

### 3.2 AI Reporting Engine (`ai_service.py` & `prompts.py`)
The AI engine aggregates the global KPI metrics (Health Score, SLA Compliance %, MTTR, Problem Backlog) and chunks them into a JSON payload. This is injected into the `FULL_EXECUTIVE_REPORT_PROMPT`, which demands a massive, 10-section, 15-page document.
- The AI interprets the data dynamically, providing root-cause hypothetical scenarios and actionable engineering runbooks.
- It leverages Mermaid.js for architecture diagrams and Unicode for visual trend charts.

### 3.3 Rich Notification Dispatcher (`notification_service.py`)
When a massive report is generated, the system alerts executives via Slack and Microsoft Teams. 
- It uses native **Slack Block Kit** (Headers, Context, Sections, Dividers) to format the KPIs beautifully.
- It uses **Microsoft Adaptive Cards** for Teams.
- It includes live dynamic dates and Unicode visual progress bars (`[█████████░] 90%`) for the 7-Day SLA Trend directly inside the Slack/Teams channel, alongside a link to download the full 15-page PDF.

### 3.4 Live WebSocket Incident Feed (`websockets.py` & `scheduler.py`)
The system proves real-time operational awareness by utilizing a background asyncio scheduler (`_inject_live_incident`) that pushes a simulated P1/P2/P3 incident into the database every 15 seconds. This event is intercepted and instantly broadcasted to all connected frontend clients via the `/api/v1/ws/dashboard` WebSocket route, causing the frontend grid to flash red without requiring a page refresh.

### 3.5 Authentication & RBAC (`auth.py` & `security.py`)
JWT-based authentication protecting the API routes. 
- **Admin (`admin` / `Admin@123`):** Full access to trigger AI report generations and purge metrics.
- **Viewer (`viewer` / `Viewer@123`):** Read-only access to the dashboards.

## 4. Connections & Network Flow
1. **User Action:** User clicks "Generate AI Report" on the React Dashboard.
2. **API Request:** Frontend fires POST to `/api/v1/reports/generate` with JWT Bearer token.
3. **Backend Auth:** FastAPI `get_admin_user` dependency verifies the token and role.
4. **Analytics Aggregation:** `AnalyticsService` queries SQLite for incidents, grouping by MTTR, SLA breaches, and Open Problem counts.
5. **AI Prompt Injection:** The JSON data is injected into the 15-page report prompt in `ai_service.py`.
6. **Gemini SDK Execution:** The backend attempts to call Google Gemini. (If offline, it generates a deterministic mock report).
7. **Report Saving:** The returned Markdown is saved to `data/reports/`, and a PDF is generated via `pdf_service.py` (markdown2 & pdfkit/wkhtmltopdf).
8. **Notification Dispatch:** `NotificationService` formats the Slack Block Kit and Teams Adaptive Card and fires the POST requests to their respective Webhook URLs.
9. **Response:** Frontend receives the download links and displays a success toast.

## 5. Setup & Execution Instructions
1. **Database Seed:** `python scripts/generate_data.py`
2. **Backend Start:** `cd backend && uvicorn main:app --host 0.0.0.0 --port 8000`
3. **Frontend Start:** `cd frontend && npm run dev`
4. **Environment Variables Needed:** `GEMINI_API_KEY`, `SLACK_WEBHOOK_URL`, `TEAMS_WEBHOOK_URL` in the root `.env` file.
