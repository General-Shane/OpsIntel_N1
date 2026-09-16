# OPSINTEL — Capgemini Enterprise Design System Specification

**Document ID:** OPSINTEL-DS-2026-004  
**Version:** 3.2 (Dual-Theme Light & Dark NOC Command Center Release)  
**Brand Foundation:** Capgemini Enterprise IT Operations  
**Target Platform:** React 19 / TypeScript / Vite / CSS Design Tokens / ReportLab PDF  

---

## 1. Brand Philosophy & Dual-Theme Architecture

OPSINTEL provides dual-theme capability tailored to distinct operational contexts:
- **Light Mode ("Executive Review"):** Clean, calm, high-clarity environment designed for executive briefings, SLA reviews, and PDF report delivery (`#F5F7FA` canvas, `#FFFFFF` cards, `#06243D` midnight sidebar).
- **Dark Mode ("NOC Command Center"):** Layered navy palette engineered for 24/7 mission-critical operations, reducing visual fatigue while accentuating abnormal telemetry and SLA risk (`#071521` canvas, `#0B1F31` cards, `#102A40` headers, `#041827` operations sidebar).
- **System Mode:** Intelligently tracks user OS `prefers-color-scheme`.

### Zero-Flash Theme Initialization
Theme state is read and applied prior to initial render via an inline DOM script in `index.html` and managed reactively with `ThemeContext.tsx` and persisted in `localStorage`.

---

## 2. Authoritative Dual-Theme Tokens (`frontend/src/index.css`)

### 2.1 Light Theme Tokens (`:root`, `[data-theme="light"]`)
```css
--cg-bg-app: #F5F7FA;               /* Application Light Background */
--cg-surface-card: #FFFFFF;         /* Crisp White Card Surface */
--cg-surface-secondary: #EEF3F7;    /* Secondary Surface / Tabs / Headers */
--cg-surface-elevated: #FFFFFF;     /* Modals / Drawers / Tooltips */
--cg-surface-hover: #F8FAFC;        /* Table Row Hover */
--cg-surface-input: #FFFFFF;        /* Input Field Background */

--text-primary: #132238;            /* Primary Deep Navy-Slate */
--text-secondary: #5F7185;          /* Secondary Slate Text */
--text-muted: #8291A3;              /* Muted Auxiliary Text & Timestamps */

--cg-navy-sidebar: #06243D;         /* Deep Navy Sidebar */
--cg-navy-sidebar-active: #0D3356;  /* Sidebar Item Active */
--cg-blue-primary: #0070AD;         /* Capgemini Primary Blue */
--cg-blue-secondary: #2F80C9;       /* Secondary Blue */
--cg-blue-soft: #EAF4FB;            /* Soft Blue (active tabs / soft pills) */
--cg-border: #D9E2EA;               /* Standard Card & Element Border */
--cg-border-strong: #C4D3E0;        /* Stronger Border */

--status-healthy: #168A63;          /* Healthy Green */
--status-healthy-bg: #E7F6F0;
--status-warning: #C88719;          /* Warning Amber */
--status-warning-bg: #FEF6E8;
--status-critical: #C94A4A;         /* Critical Red */
--status-critical-bg: #FDEEEE;
--status-info: #2F80C9;             /* Informational Blue */
--status-info-bg: #EAF4FB;
```

### 2.2 Dark Theme Tokens (`[data-theme="dark"]`, `.dark`)
```css
--cg-bg-app: #071521;               /* Deepest Operations Canvas */
--cg-surface-card: #0B1F31;         /* Primary Surface Cards */
--cg-surface-secondary: #102A40;    /* Secondary Surface / Tabs / Headers */
--cg-surface-elevated: #14344D;     /* Elevated Surfaces / Modals / Tooltips */
--cg-surface-hover: #10283d;        /* Table Row Hover */
--cg-surface-input: #081927;        /* Input Field Background */

--text-primary: #F4F7FA;            /* Crisp High-Contrast Light Slate */
--text-secondary: #A9BAC8;          /* Soft Slate Secondary */
--text-muted: #7F95A6;              /* Muted Timestamps & Secondary */

--cg-navy-sidebar: #041827;         /* Operations Sidebar */
--cg-navy-sidebar-active: #0f3554;  /* Sidebar Item Active */
--cg-blue-primary: #0070AD;         /* Capgemini Primary Blue */
--cg-blue-secondary: #2F80C9;       /* Secondary Blue */
--cg-blue-soft: rgba(0, 112, 173, 0.18); /* Soft Blue Highlight */
--cg-border: rgba(255, 255, 255, 0.10); /* Subtle Border */
--cg-border-strong: rgba(255, 255, 255, 0.18); /* Strong Border */

--status-healthy: #168A63;
--status-healthy-bg: rgba(22, 138, 99, 0.18);
--status-warning: #C88719;
--status-warning-bg: rgba(200, 135, 25, 0.18);
--status-critical: #C94A4A;
--status-critical-bg: rgba(201, 74, 74, 0.18);
--status-info: #2F80C9;
--status-info-bg: rgba(47, 128, 201, 0.18);
```

---

## 3. Global Theme Switcher (`TopHeader.tsx` & `ProfileView.tsx`)

The theme switcher is embedded directly into the global command header and user profile settings:
- **`Sun` (Light):** Immediate switch to light executive view.
- **`Moon` (Dark):** Immediate switch to layered dark navy NOC command view.
- **`Monitor` (System):** Auto-synchronizes with operating system preference via `window.matchMedia`.

---

## 4. Chart & Data Visualization Theming

All Recharts data visualizations automatically inherit theme variables:
- **Grid Lines:** `var(--chart-grid)` (`#EEF3F7` in light, `rgba(255,255,255,0.07)` in dark).
- **Tooltip Containers:** `var(--chart-tooltip-bg)` with `var(--chart-tooltip-border)` and `var(--chart-tooltip-shadow)`.
- **Axis & Labels:** `var(--text-muted)` and `var(--text-secondary)`.

---
*Specification validated against production build, E2E test suites, and theme persistence checks.*
