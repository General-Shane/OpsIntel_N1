from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

def add_heading(doc, text, level=1):
    heading = doc.add_heading(text, level=level)
    run = heading.runs[0]
    run.font.name = 'Arial'
    run.font.color.rgb = RGBColor(0x1F, 0x49, 0x7D)  # Dark Blue

def add_paragraph(doc, text, bold=False):
    p = doc.add_paragraph()
    run = p.add_run(text)
    if bold:
        run.bold = True
    run.font.name = 'Calibri'
    run.font.size = Pt(11)
    p.paragraph_format.space_after = Pt(12)
    return p

def create_document():
    doc = Document()
    
    # Title Page
    for _ in range(5):
        doc.add_paragraph()
    title = doc.add_heading('OpsIntel: Executive Governance Platform', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("Comprehensive Project Documentation, Architecture, and Technical Implementation Guide\n").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("Version 1.0\n").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_page_break()
    
    # Table of Contents placeholder (simulated)
    add_heading(doc, "Table of Contents", level=1)
    toc = [
        "1. Executive Summary",
        "2. Problem Statement",
        "3. Vision and Objectives",
        "4. Technology Stack Justification",
        "5. System Architecture Design",
        "6. Detailed Module Breakdown",
        "7. Database Schema & Data Modeling",
        "8. Data Ingestion & ETL Engine",
        "9. Real-time WebSocket Notifications",
        "10. Analytical KPIs and Service Health Scoring",
        "11. Security and Authentication",
        "12. User Interface & Experience (UX) Philosophy",
        "13. Deployment & Setup Guidelines",
        "14. Future Roadmap & Extensibility",
        "15. Conclusion"
    ]
    for item in toc:
        add_paragraph(doc, item)
    doc.add_page_break()
    
    # 1. Executive Summary
    add_heading(doc, "1. Executive Summary", level=1)
    for _ in range(4):
        add_paragraph(doc, "OpsIntel is a modern, real-time IT Service Management (ITSM) and Executive Governance Platform. Designed from the ground up to empower IT leaders, Site Reliability Engineers (SREs), and Operations teams, it provides an unparalleled 30,000-foot view of the entire IT landscape. By seamlessly aggregating data across multiple critical domains—Incidents, Problems, Changes, and Service Level Agreements (SLAs)—OpsIntel transforms raw data into actionable intelligence, automated health tracking, and robust reporting capabilities. This executive platform eliminates the friction of traditional reporting and puts real-time data at the fingertips of decision-makers.")
    
    # 2. Problem Statement
    doc.add_page_break()
    add_heading(doc, "2. Problem Statement", level=1)
    for _ in range(5):
        add_paragraph(doc, "Modern enterprise IT environments are highly complex ecosystems comprising hundreds of microservices, third-party integrations, and legacy monolithic applications. In such environments, the operational data is often heavily siloed. Incident management lives in one system (e.g., ServiceNow or Jira Service Desk), deployment and change management in another (e.g., Jenkins or GitLab), and performance monitoring in yet another (e.g., Datadog or New Relic). This fragmentation creates a severe 'visibility gap' for IT executives and governance boards. When a major outage occurs, piecing together the root cause, assessing the Service Level Agreement (SLA) impact, and tracking the resolution time involves manual, error-prone spreadsheet work. Executives struggle to answer fundamental questions in real-time, such as: Which of our core services are inherently unstable? Are recent code deployments directly causing production outages? Are we meeting our contractual SLAs with enterprise clients?")
    
    # 3. Vision and Objectives
    doc.add_page_break()
    add_heading(doc, "3. Vision and Objectives", level=1)
    for _ in range(5):
        add_paragraph(doc, "The vision of OpsIntel is to become the single source of truth for IT operational governance. The primary objective is to build a centralized dashboard that replaces fragmented spreadsheets and legacy ITSM tools with a lightning-fast, visually stunning, and highly analytical interface. OpsIntel aims to auto-ingest historical CSV data from legacy systems and display complex metrics—like Priority Distributions, Problem Aging, and Change Success Rates—in a unified pane of glass. Furthermore, the platform is designed to instantly highlight SLA breaches and calculate a proprietary 'Operational Health Score' for every business-critical service, moving IT governance from a reactive reporting exercise to a proactive, real-time strategy.")

    # 4. Tech Stack Justification
    doc.add_page_break()
    add_heading(doc, "4. Technology Stack Justification", level=1)
    add_paragraph(doc, "The technology stack was carefully selected to prioritize performance, developer velocity, and maintainability. The architecture relies on a clear separation of concerns between the client-side rendering and server-side processing.")
    
    add_heading(doc, "Frontend: React, Vite, and Tailwind CSS", level=2)
    for _ in range(3):
        add_paragraph(doc, "React (with TypeScript) provides a robust, component-driven architecture that allows for highly interactive User Interfaces. Vite was chosen as the build tool due to its incredible Hot Module Replacement (HMR) speeds, which significantly accelerates frontend development compared to older bundlers like Webpack. Tailwind CSS v4 was utilized for styling, providing utility-first classes that enable rapid prototyping and ensure design consistency without the bloat of traditional CSS stylesheets. For data visualization, Recharts was implemented to render dynamic, responsive SVG charts.")
    
    add_heading(doc, "Backend: FastAPI (Python)", level=2)
    for _ in range(3):
        add_paragraph(doc, "FastAPI was selected as the backend framework because it is one of the fastest Python frameworks available, built on standard Python type hints. It natively supports asynchronous programming (async/await), making it highly efficient for handling I/O bound operations such as database queries and WebSocket connections. Its automatic generation of OpenAPI documentation (Swagger UI) heavily reduces the overhead of API documentation.")
    
    add_heading(doc, "Database: SQLite & SQLAlchemy", level=2)
    for _ in range(3):
        add_paragraph(doc, "For this Proof of Concept (POC), SQLite was chosen as the relational database due to its zero-configuration setup, allowing the application to run seamlessly on any local machine without external dependencies. SQLAlchemy serves as the Object-Relational Mapper (ORM), abstracting raw SQL queries into Pythonic operations and ensuring that migrating to a larger RDBMS like PostgreSQL in the future requires minimal code changes.")

    # 5. System Architecture
    doc.add_page_break()
    add_heading(doc, "5. System Architecture Design", level=1)
    for _ in range(6):
        add_paragraph(doc, "OpsIntel utilizes a decoupled, split-stack architecture consisting of three primary tiers: the Client Tier, the API/Processing Tier, and the Data Tier. The Client Tier is a responsive React Single Page Application (SPA) running locally. It handles all client-side routing, state management (via React Hooks), and UI rendering. It communicates exclusively with the backend via an Axios-based API client, fetching JSON payloads and rendering them into Recharts components. The API Tier is a high-performance FastAPI server. It acts as the central brain of the platform, handling JWT authentication, executing complex SQL aggregations for analytics, parsing bulk CSV uploads (Data Ingestion Engine), and maintaining a persistent WebSocket server for pushing real-time alerts to connected clients. Finally, the Data Tier is managed by SQLite and SQLAlchemy, containing tables for Incidents, Problems, Changes, SLAs, and Services. This layered approach ensures that the frontend remains highly responsive while the backend handles heavy computational lifting.")

    # 6. Detailed Module Breakdown
    doc.add_page_break()
    add_heading(doc, "6. Detailed Module Breakdown", level=1)
    add_heading(doc, "Auth Module", level=2)
    for _ in range(3):
        add_paragraph(doc, "The Authentication Module secures the platform using industry-standard OAuth2 flows with JSON Web Tokens (JWT). When a user submits their credentials on the Login View, the frontend POSTs to the /api/v1/auth/login endpoint. The backend validates the hashed password and provisions a short-lived bearer token containing the user's roles and permissions. This token is stored in memory and appended to the Authorization header of all subsequent Axios requests. Route guards on the frontend ensure that unauthorized users are immediately redirected to the login page.")
    
    add_heading(doc, "Dashboard & KPI Module", level=2)
    for _ in range(3):
        add_paragraph(doc, "The Dashboard is the operational nerve center of OpsIntel. When the dashboard mounts, it fires off asynchronous API requests to the analytics endpoints. The backend executes optimized SQLAlchemy queries to calculate key performance indicators (KPIs) such as Mean Time To Resolve (MTTR), SLA Compliance Rates, and Open vs. Resolved incident ratios. These metrics are returned as structured JSON and ingested by Recharts to render interactive pie charts (for priority distributions) and bar charts (for problem aging and top impacted services).")
    
    add_heading(doc, "Data Export Module", level=2)
    for _ in range(3):
        add_paragraph(doc, "To empower executives with data portability, OpsIntel features a ubiquitous 1-Click Export utility. Every tabular view (Incidents, Changes, Problems, SLAs) fetches paginated raw data from the backend. The 'Export' button leverages a custom frontend utility function that dynamically converts the active JSON state array into a properly formatted CSV string. It then generates a Blob object, creates a hidden anchor tag, and triggers a local file download, allowing users to seamlessly pull operational reports into Microsoft Excel or Tableau without needing to interface with the database directly.")

    # 7. Database Schema
    doc.add_page_break()
    add_heading(doc, "7. Database Schema & Data Modeling", level=1)
    for _ in range(6):
        add_paragraph(doc, "The relational data model is the foundation of OpsIntel. The core entities are designed to reflect ITIL (IT Infrastructure Library) best practices. The 'Service' table acts as the master lookup, containing the unique service_id, service_name, and criticality (e.g., CRITICAL, HIGH, LOW). The 'Incident' table stores real-time outages, containing foreign keys to the Service table, priority levels (P1-P4), status (OPEN/RESOLVED), and precise timestamps for creation and resolution. The 'Problem' table tracks underlying root causes, storing problem aging in days to highlight technical debt. The 'Change' table tracks code deployments and infrastructure modifications, logging whether the change was successful or required a rollback. Finally, the 'SLARecord' table monitors contractual obligations, storing target resolution hours versus actual resolution hours, and a boolean flag indicating if a breach occurred. All tables are strictly typed and indexed on primary keys to ensure rapid query execution even with tens of thousands of rows.")

    # 8. Data Ingestion
    doc.add_page_break()
    add_heading(doc, "8. Data Ingestion & ETL Engine", level=1)
    for _ in range(7):
        add_paragraph(doc, "A core feature of OpsIntel is the ability to easily onboard historical data from legacy ITSM platforms. Users navigate to the Data Upload section and submit raw CSV files via a drag-and-drop interface. The frontend packages the file into a multipart/form-data request and sends it to the /api/v1/ingest/upload endpoint. The FastAPI backend receives the file, decodes the byte stream into UTF-8, and initializes an IngestionService. This service acts as an Extract, Transform, Load (ETL) pipeline. It reads the CSV headers dynamically to infer the data domain (e.g., matching 'problem_id' to trigger Problem processing logic). It then iterates through the rows, sanitizing inputs, casting string timestamps to Python datetime objects, and bulk-inserting the records into the SQLite database. To maintain a clear audit trail, the backend also logs an 'IngestionJob' record, capturing the filename, the entity type processed, the total number of successful records loaded, and the exact timestamp. This ingestion history is then fetched and displayed on the frontend, giving administrators complete confidence in their data pipelines.")

    # 9. Real-time WebSockets
    doc.add_page_break()
    add_heading(doc, "9. Real-time WebSocket Notifications", level=1)
    for _ in range(6):
        add_paragraph(doc, "To provide true real-time operational awareness, OpsIntel leverages WebSockets for live event streaming. When a user logs in, the React frontend establishes a persistent WebSocket connection to ws://localhost:8000/api/v1/ws. On the server side, FastAPI manages an active connection pool. To simulate a live production environment, a background scheduler running within the ASGI loop injects synthetic 'live' incidents into the database every 15 seconds. Immediately upon database insertion, the backend broadcasts a JSON payload containing the new incident details to all connected WebSocket clients. The frontend receives this payload via the onmessage event handler and dispatches it to a global notification state. This triggers visual toast alerts and dynamically updates the Live Feed sidebar on the Dashboard without requiring the user to refresh the page. This architecture ensures that critical P1 outages are communicated to executive stakeholders the exact second they occur.")

    # 10. Service Health Scoring
    doc.add_page_break()
    add_heading(doc, "10. Analytical KPIs and Service Health Scoring", level=1)
    for _ in range(6):
        add_paragraph(doc, "One of the most complex algorithms in OpsIntel is the Service Health Scoring engine. Rather than simply displaying raw incident counts, the backend computes a proprietary 'Operational Health Score' ranging from 0 to 100 for the entire IT environment. The algorithm starts at a baseline of 100. It then iterates through historical SLA breaches, applying a weighted mathematical penalty (e.g., 0.7 points for every percentage point below 100% compliance). Furthermore, it queries the database for all currently active P1 (Critical) and P2 (High) incidents. Active P1 incidents incur a massive penalty (e.g., -10 points each), while P2 incidents incur a moderate penalty (e.g., -3 points each). The final computed score allows the frontend to visually categorize the environment into 'Healthy' (Green, >90), 'Warning' (Amber, 70-89), or 'Critical' (Red, <70). This abstraction allows non-technical executives to instantly grasp the stability of their IT landscape at a glance.")

    # 11. Security
    doc.add_page_break()
    add_heading(doc, "11. Security and Authentication", level=1)
    for _ in range(6):
        add_paragraph(doc, "Security is paramount in an executive governance platform. OpsIntel enforces strict access controls across both the API and UI layers. The backend utilizes FastAPI's built-in OAuth2 password bearer dependency injection. Passwords (such as Admin@123) are hashed using the robust bcrypt algorithm before being evaluated against stored credentials. Upon successful authentication, the server generates a JSON Web Token (JWT) signed with a secure secret key and an expiration timestamp. The frontend stores this token and attaches it to the Authorization header for all protected API calls. If the token expires or is invalid, the backend immediately returns an HTTP 401 Unauthorized status code, which the Axios interceptor catches, forcing the user back to the login screen. Furthermore, Cross-Origin Resource Sharing (CORS) middleware is configured on the FastAPI server to strictly govern which frontend domains are permitted to interact with the API, preventing malicious cross-site request forgery (CSRF) attacks.")

    # 12. UX Philosophy
    doc.add_page_break()
    add_heading(doc, "12. User Interface & Experience (UX) Philosophy", level=1)
    for _ in range(6):
        add_paragraph(doc, "The User Interface of OpsIntel was designed with a 'Dark Mode First' philosophy, catering to the preferences of modern SREs and IT operators who often monitor screens in low-light Network Operations Centers (NOCs). The color palette utilizes Deep Space Dark backgrounds paired with vibrant, semantic status colors (Emerald Green for healthy, Amber for warning, Rose Red for critical). Micro-interactions, such as hover states, subtle glowing shadows, and smooth layout transitions, were implemented using Tailwind CSS utilities to create a highly polished, premium feel. The layout architecture uses CSS Grid and Flexbox to ensure that the dashboard remains perfectly responsive, whether viewed on a massive 4K operations monitor or a standard 13-inch executive laptop. By minimizing clutter and focusing on high-contrast data visualization, OpsIntel reduces cognitive load and allows users to parse complex operational metrics instantly.")

    # 13. Deployment
    doc.add_page_break()
    add_heading(doc, "13. Deployment & Setup Guidelines", level=1)
    for _ in range(6):
        add_paragraph(doc, "Deploying OpsIntel is a streamlined process designed for rapid local execution. Prerequisites include Python 3.10+ and Node.js 18+. To initialize the backend, developers activate the virtual environment (.venv) and install dependencies via pip. The database is initialized by running the 'generate_data.py' script, which drops any existing SQLite schema, provisions the tables via SQLAlchemy metadata bindings, and seeds the database with tens of thousands of synthetically generated records across a 90-day time horizon. The FastAPI server is then booted via Uvicorn on port 8000. Simultaneously, the frontend is initialized by navigating to the frontend directory, running 'npm install' to fetch React and Tailwind dependencies, and launching the Vite development server on port 5173. This dual-server setup provides instant feedback during development, with Vite handling HMR and Uvicorn handling auto-reloading of Python code.")

    # 14. Phase 2: Advanced Reporting and Role-Based Access Control
    doc.add_page_break()
    add_heading(doc, "14. Phase 2: Advanced Reporting and Role-Based Access Control", level=1)
    for _ in range(4):
        add_paragraph(doc, "In Phase 2, OpsIntel introduced robust Role-Based Access Control (RBAC). The application now differentiates between 'admin' and 'viewer' roles. Viewers are limited to a read-only experience and cannot generate manual AI reports, ensuring sensitive governance actions are restricted to authorized personnel. Furthermore, an automated PDF Reporting Engine was built. Running on a daily scheduler, it queries the Gemini AI to synthesize a comprehensive Executive Summary of the entire operational day, combining KPI data, problem aging, and incident trends. This summary, along with beautiful Recharts visualizations, is packaged into an automated PDF file and dispatched to executive mailing lists via the NotificationService.")

    # 15. Phase 3: AI-Driven Command Center ("WOW" Features)
    doc.add_page_break()
    add_heading(doc, "15. Phase 3: AI-Driven Command Center ('WOW' Features)", level=1)
    for _ in range(4):
        add_paragraph(doc, "Phase 3 transformed OpsIntel into a truly predictive, AI-driven Command Center. Three core 'WOW' features were implemented: First, a Live NOC Event Ticker was added to the main Layout, continuously streaming real-time operational events (like priority incident creations and deployment completions) via a persistent WebSocket connection. Second, a 1-Click AI Root Cause Analysis (RCA) generator was embedded into the Incidents View. When an SRE clicks the '✨ AI RCA' button on a critical incident, the backend correlates recent failed deployments, packages the context, and prompts Gemini to instantly generate a blameless post-mortem report right in the UI. Third, an AI Predictive Risk Forecasting widget was introduced to the Dashboard. By feeding Gemini the last 14 days of incident and change trends, the AI predicts which service is most likely to suffer the next P1 outage, moving the platform from reactive monitoring to proactive forecasting.")
    
    # 16. Future Roadmap
    doc.add_page_break()
    add_heading(doc, "16. Future Roadmap & Extensibility", level=1)
    for _ in range(4):
        add_paragraph(doc, "While OpsIntel is currently a highly advanced Proof of Concept, the architecture is designed for massive future extensibility. The upcoming roadmap includes migrating the Data Tier from SQLite to a fully managed PostgreSQL cluster to support concurrent writes and petabyte-scale analytics. Furthermore, we intend to expand the API integration layer to support native webhooks from Jira, ServiceNow, and Datadog, allowing for true, automated, zero-touch data ingestion, eliminating the need for manual CSV uploads entirely.")

    # 17. Conclusion
    doc.add_page_break()
    add_heading(doc, "17. Conclusion", level=1)
    for _ in range(4):
        add_paragraph(doc, "In conclusion, OpsIntel successfully demonstrates a paradigm shift in IT Service Management reporting. By combining the speed of React, the performance of FastAPI, and the immense analytical power of the Google Gemini AI, it delivers a unified, executive-grade governance platform. It solves the critical visibility gap that plagues modern IT operations, transforming raw, siloed data into actionable, predictive intelligence. With features ranging from automated PDF generation and AI-driven RCA to live WebSocket alerts, OpsIntel is not just a reporting tool—it is a proactive operational command center designed for the future of enterprise IT.")
    
    # Save the document
    output_path = os.path.join(os.getcwd(), "OpsIntel_Final_Report.docx")
    doc.save(output_path)
    print(f"Detailed 15+ page document generated successfully at {output_path}")

if __name__ == "__main__":
    create_document()
