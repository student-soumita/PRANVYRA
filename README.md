# PRANVYRA (प्राणवायरा)
## Every Breath. A Better Tomorrow.
### Open-Access AI Urban Air Intelligence & Sustainable Lifestyle Platform

[![Python 3.12](https://img.shields.io/badge/Python-3.12-16A88A.svg)](https://python.org)
[![Flask REST API](https://img.shields.io/badge/Flask-3.1-123D35.svg)](https://flask.palletsprojects.com/)
[![Open Environmental Data](https://img.shields.io/badge/Data-Open--Meteo%20CAMS-B9E8D7.svg)](https://open-meteo.com)
[![GHG Methodology](https://img.shields.io/badge/Factors-UK%20DEFRA%20%7C%20US%20EPA-E7A83E.svg)](https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting)
[![Tests Passing](https://img.shields.io/badge/Tests-46%2F46%20Passing-16A88A.svg)](tests/)

---

## 1. PRODUCT VISION & OPEN-ACCESS ARCHITECTURE

PRANVYRA is a public-access, hyperlocal AI-powered environmental intelligence platform. Unlike conventional air dashboards that display passive numbers or require cumbersome account registration, **PRANVYRA is 100% open-access**:

- **No Mandatory Login or Registration:** Any person can open the platform, detect their location or enter a city, and immediately access their environmental intelligence.
- **Zero Demo Accounts or Seed Personas:** No hardcoded sample users, fake monitoring stations, or simulated customer statistics.
- **Session Continuity via Persistent Visitor UUID:** Immediate full persistence for personal routines, indoor audits, clean route trips, and impact receipts using client-stored `X-Visitor-Id` headers.
- **Optional Cloud Sync:** Optional registration is provided solely for cross-device backup, never as a gate for basic environmental knowledge.

> **Core Philosophy:** *Don't just show pollution. Help people act against it.*

---

## 2. FIVE ORIGINAL INTELLIGENCE FEATURES

### Feature A: AIR-TWIN — Adaptive Personal Environmental Intelligence
- **Dynamic Resilience Gauge:** An adaptive exposure resilience score (0–100) combining ambient air quality, primary transport mode shielding, and indoor ventilation factors.
- **Commute Vulnerability Assessment:** Evaluates physical intake (e.g. unshielded two-wheelers vs grade-separated electric rail).
- **Adaptive Daily Windows:** Recommends optimal cross-ventilation hours (e.g. midday solar thermal mixing) and exercise windows based on diurnal inversion curves.
- **Scientific Honesty:** Clearly labeled as an educational exposure model, not a medical or clinical diagnosis.

### Feature B: BREATHROUTE — Environmentally Aware Journey Planner
- **Multi-Modal Comparison:** Compares 7 distinct travel modes (Walking, Cycling, Electric Metro, Electric Bus, CNG Auto, Motorcycle, Petrol Car) by travel time, direct tailpipe emissions, and street-level exposure risk.
- **Route Intelligence:** Recommends optimal travel times and modes to avoid rush-hour surface toxic corridors.
- **One-Click Decision Logging:** Issues an official **Personal Impact Receipt** when the user chooses a clean transit mode.

### Feature C: LIFE-SWITCH — Environmental What-If Decision Engine
An interactive lifestyle transition simulator featuring 5 real-world switches:
1. **Mobility Switch:** Solo motorcycle to Electric Metro (~430 kg CO₂e/year avoided).
2. **Waste & Production Switch:** Single-use PET bottles to reusable stainless steel flasks (~78 kg CO₂e/year avoided).
3. **Home Climate Switch:** Air conditioner thermostat setpoint adjustment from 20°C to 24°C (~177 kg CO₂e/year avoided).
4. **Kitchen Health Switch:** LPG/biomass cooking with forced exhaust discipline (~120 kg CO₂e/year avoided).
5. **Urban Carpool Switch:** Solo passenger car travel to shared carpooling (~730 kg CO₂e/year avoided).
- **Full Scientific Transparency:** Displays exact mathematical formulas, UK DEFRA 2023 conversion factors, and boundary limitations.

### Feature D: NEIGHBORHOOD PULSE — Honest Community Participation Ledger
- **Real Aggregated Collective Metrics:** Live ledger displaying genuine citizen actions, total CO₂e avoided, active participants, and completed challenges.
- **Zero Fabricated Stats:** Metrics are derived strictly from database records (`impact_logs` and `user_challenge_participation`).
- **Community Challenges:** Real milestone challenges (e.g., *Metro Master*, *Zero Idle Hero*, *Air Alchemist*, *Cycle Vanguard*) that award verified badges.

### Feature E: PRANVYRA INTELLIGENCE CORE — Multi-Role Environmental AI
PRANVYRA operates as a unified, context-aware AI intelligence system powered by 5 specialized expert roles and an intelligent intent-routing architecture:

1. **Atmospheric Scientist:**
   - *Scope:* US EPA AQI interpretation, PM2.5/PM10 particulate dynamics, NO₂, O₃, CO, SO₂, boundary layer meteorology, thermal inversions, and atmospheric dispersion.
   - *Capability:* Diagnoses atmospheric stagnation, explains pollutant physics, and suggests time-calibrated outdoor precautions.
2. **Urban Mobility & Emission Expert:**
   - *Scope:* Sustainable commuting, UK DEFRA 2023 modal emission comparisons, grade-separated rail transit, active travel, and roadside exposure mitigation.
   - *Capability:* Computes avoided kilograms of CO₂e per trip, transparent calculation methodologies, and transit shift recommendations.
3. **Indoor Air Quality Specialist:**
   - *Scope:* Indoor ventilation rates, cooking exhaust (NO₂/PM2.5 from LPG/biomass), dust resuspension, mechanical HEPA filtration (H13/H14), and infiltration control.
   - *Capability:* Conducts built-environment audits, debunks indoor myths (e.g., houseplants do NOT filter PM2.5), and advises on ventilation timing.
4. **Sustainability Strategist:**
   - *Scope:* Realistic lifestyle shifts, household energy conservation (AC thermostat calibration), single-use plastic reduction, and carbon footprint mitigation.
   - *Capability:* Suggests high-leverage, affordable, habit-based switches with quantified annual savings.
5. **Environmental Research Analyst:**
   - *Scope:* Atmospheric telemetry datasets (Open-Meteo CAMS), diurnal curve comparisons, scientific uncertainty evaluation, and sensor vs. model disclosures.
   - *Capability:* Interprets trends, highlights satellite grid resolution limitations, and provides honest evidence-based context.

- **Intelligent Intent-Routing & Cross-Domain Synthesis:** The router automatically classifies user prompts into the optimal expert role or synthesizes cross-domain multi-expert responses (e.g., cycling in polluted air synthesizes both Mobility and Atmospheric expertise).
- **Auto & Manual UI Selector:** Visitors can let the system automatically route their query or manually pin their inquiry to any of the 5 expert roles via the chat dropdown.
- **Context-Aware Multi-Turn Conversational Memory:** The assistant retains the last 8 conversation turns and environmental telemetry, enabling seamless natural follow-ups ("Can I go jogging this evening?") without repeating city or pollutant parameters.
- **Dynamic Follow-Up Suggestion Generator:** Dynamically generates 3 contextual follow-up chips per query in the user's selected language.
- **Structured Advice Blueprint Cards:** Complex inquiries output a structured advice card detailing:
  1. *Recommended Action*
  2. *Problem Identified*
  3. *Scientific Reason*
  4. *Expected Benefit*
  5. *Estimated Impact*
  6. *Confidence Level & Verified Source*

---

## 3. CENTRALIZED MULTILINGUAL i18n SYSTEM
PRANVYRA features an architectural-level internationalization engine (`window.PranvyraI18n`) supporting **English (`en`)**, **Hindi (`hi` - हिंदी)**, and **Bengali (`bn` - বাংলা)**:

- **100% Full-DOM Real-Time Translation:** Translates every section, card, modal, button, placeholder, and educational text without page reload.
- **Complete Key Parity:** 195+ translation keys maintained with 100% parity across `en.json`, `hi.json`, and `bn.json`.
- **Dynamic Attribute Mapping:** Uses `data-i18n`, `data-i18n-placeholder`, `data-i18n-title`, and `data-i18n-aria` attributes, preserving Lucide icon sub-nodes.
- **Authentic Native Terminology:** Written by environmental linguists, avoiding literal translation artifacts or broken phrasing.
- **Native Typography:** Interweaves Google Fonts `Noto Sans Devanagari` and `Noto Sans Bengali` into the core typography stack for authentic rendering.

---

## 4. FEATURE 6: PERSONAL IMPACT RECEIPT

Every verified clean journey logged in **BreathRoute** or habit commitment made in **Life-Switch** issues an official, verifiable **Personal Impact Receipt**:

- **Unique Receipt ID:** Formatted as `PRAN-RCPT-XXXXXXXX`.
- **Decision Taken & Comparison:** Explicit "Before (Baseline)" vs "After (Adopted)" accounting.
- **Avoided Emissions:** Quantified in kg CO₂e with UK DEFRA 2023 conversion factors.
- **Educational Notice:** Explicitly labeled as estimated personal avoided emissions, not a physical sensor measurement of citywide air quality.
- **Print & PDF Export:** One-click `window.print()` formatted stylesheet for printing or saving official PDF documentation.

---

## 5. SCIENTIFIC METHODOLOGY & DATA SOURCES

PRANVYRA adheres strictly to open, peer-reviewed environmental science:

| Domain | Source / Standard | Methodology Details |
|---|---|---|
| **Air Quality Index** | **US EPA AQI (40 CFR Part 58)** | Piecewise linear sub-index interpolation across PM2.5, PM10, NO₂, O₃, CO, and SO₂. |
| **Atmospheric Data** | **Open-Meteo CAMS Global Model** | European Copernicus Atmosphere Monitoring Service reanalysis & satellite assimilation. |
| **Meteorology** | **Open-Meteo High-Resolution Weather** | Boundary layer wind vector, temperature, relative humidity, and WMO weather codes. |
| **Transportation Factors** | **UK DEFRA / DESNZ 2023** | Car (170.5 g/km), Motorcycle (103.2 g/km), Bus (96.5 g/pkm), Metro (28.5 g/pkm). |
| **Indoor Science** | **ASHRAE 62.1 & 62.2** | Ventilation rate standards, particulate infiltration physics, and HEPA CADR sizing. |

---

## 6. REPOSITORY STRUCTURE

```
PranVyra/
│
├── run.py                         # Application entry point (python run.py)
├── app.py                         # Flask factory & blueprint registration
├── config.py                      # Application configuration & API endpoints
├── conftest.py & pytest.ini       # Automated test suite configuration
├── requirements.txt               # Dependencies
├── .env.example                   # Environment variable template
│
├── database/
│   ├── schema.sql                 # Open-access relational DDL (visitor_profiles, receipts, chat_history, etc.)
│   ├── db.py                      # SQLite connector with get_or_create_visitor()
│   └── pranvyra.db                # Persistent database
│
├── services/
│   ├── expert_router.py           # Intelligent intent classifier & 5 expert role definitions
│   ├── ai_orchestrator.py         # Multi-role AI reasoning, Gemini integration & structured fallback
│   ├── environmental_context.py   # Multi-turn history, live telemetry & profile context injection
│   ├── air_quality.py             # Open-Meteo CAMS integration & US EPA standard
│   ├── weather.py                 # Meteorology & geocoding city search
│   ├── air_twin.py                # Adaptive resilience scoring & exposure modeling
│   ├── breath_route.py            # Haversine journey planner & multi-modal comparison
│   ├── life_switch.py             # 5 What-If habit switches & transparent math
│   ├── impact_receipt.py          # Verifiable PRAN-RCPT-XXXXXXXX generator
│   ├── impact_calculator.py       # UK DEFRA GHG emission calculations
│   └── recommendation_engine.py   # AIRWISE rule engine & Breath Budget
│
├── routes/
│   ├── api_dashboard.py           # /api/dashboard/overview, /api/dashboard/cities
│   ├── api_assistant.py           # /api/assistant/chat, /api/assistant/experts, /api/assistant/history
│   ├── api_breath_route.py        # /api/breath-route/plan, /api/breath-route/commit-trip
│   ├── api_life_switch.py         # /api/life-switch/catalog, /api/life-switch/simulate
│   ├── api_impact.py              # /api/impact/summary, /api/impact/receipts
│   ├── api_community.py           # /api/community/pulse, /api/community/challenges
│   ├── api_indoor.py              # /api/indoor/check, /api/indoor/latest
│   ├── api_planner.py             # /api/planner/today, /api/planner/toggle
│   └── api_user.py                # /api/user/air-twin, /api/user/profile, /api/user/register
│
├── templates/
│   └── index.html                 # Unified single-page application shell (11 views)
│
├── static/
│   ├── css/
│   │   ├── style.css              # Typography, dark/light theme variables, glassmorphic layout
│   │   └── modules.css            # Component styles, receipts, printable media queries
│   ├── js/
│   │   ├── i18n/
│   │   │   ├── language.js        # Centralized window.PranvyraI18n DOM translation engine
│   │   │   ├── en.json            # English translation dictionary (195+ keys)
│   │   │   ├── hi.json            # Native Hindi Devanagari dictionary (195+ keys)
│   │   │   └── bn.json            # Native Bengali dictionary (195+ keys)
│   │   ├── state.js               # Reactive global state store with visitor UUID
│   │   ├── api.js                 # REST client injecting X-Visitor-Id header
│   │   ├── assistant.js           # PRANVYRA Intelligence Core & expert selection controller
│   │   ├── breathroute.js         # BreathRoute journey planner controller
│   │   ├── lifeswitch.js          # Life-Switch simulator controller
│   │   ├── airtwin.js             # Air-Twin profile controller
│   │   ├── impact.js              # Impact tracker & receipt modal controller
│   │   ├── community.js           # Neighborhood Pulse controller
│   │   ├── dashboard.js           # Real-time AQI & weather renderer
│   │   ├── planner.js             # Daily routine planner controller
│   │   ├── indoor.js              # Indoor air audit controller
│   │   ├── map.js                 # Leaflet.js interactive atmospheric map
│   │   ├── charts.js              # Chart.js diurnal trends & modal comparisons
│   │   └── app.js                 # View router, geolocation, and city search
│   └── assets/
│       └── logo.svg               # Original PRANVYRA identity symbol
│
└── tests/
    ├── test_ai_intelligence.py    # 5 expert roles, multi-expert routing & conversational memory
    ├── test_i18n_dictionaries.py  # Trilingual dictionary parity & validation tests
    ├── test_air_quality.py        # Sub-index breakpoints & truthful offline state
    ├── test_impact.py             # DEFRA GHG emission calculations
    ├── test_recommendations.py   # AIRWISE logic & indoor scoring tests
    ├── test_api_routes.py         # All REST API endpoints & receipt generation
    └── verify_server.py           # End-to-end smoke test verification (12 capabilities)
```

---

## 7. QUICK START & INSTALLATION

### Prerequisites
- Python 3.10+
- Modern Web Browser (Chrome, Edge, Firefox, Safari)

### Setup Instructions

1. **Clone & Navigate:**
   ```bash
   cd PranVyra
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the Database:**
   ```bash
   python database/db.py
   ```

4. **Run the Automated Test Suite:**
   ```bash
   pytest -v
   ```
   *Expected Output: 46 passed in ~3.4s.*

5. **Run the 12-Point Smoke Test Verification:**
   ```bash
   python tests/verify_server.py
   ```

6. **Start the Live Web Server:**
   ```bash
   python run.py
   ```
   *Open your browser and navigate to:* **`http://127.0.0.1:5000`**

---

## 8. USER EVALUATION GUIDE

When opening `http://127.0.0.1:5000`:

1. **Open-Access Entry:** Notice there is **no login prompt**. Simply type your city (e.g. *New Delhi*, *Bengaluru*, *London*, or *New York*) or click **"Auto-Detect My Current Location"**.
2. **Air Intelligence (`#dashboard`):** View real-time AQI, the color spectrum gauge, 6 individual pollutant cards with WHO reference bars, the interactive Leaflet map, and 24-hour diurnal trend charts.
3. **Multilingual Switcher:** Click the **EN / हिंदी / বাংলা** language selector in the top bar. Observe the entire DOM dynamically translate across all modules, cards, and buttons without page reload.
4. **PRANVYRA Intelligence Core (`#assistant`):**
   - Leave the Expert Role dropdown on **Auto Expert Router** or switch to any of the 5 roles (*Atmospheric Scientist*, *Urban Mobility*, *Indoor Air*, *Sustainability Strategist*, *Environmental Analyst*).
   - Test natural questions like: *"Why does winter temperature inversion trap smoke?"* or *"Compare bicycle vs car emissions."*
   - Notice the dynamic active expert badge, structured advice cards, and contextual follow-up chips.
   - Send follow-up messages like *"Can I go jogging tonight?"* without restating your city or AQI — conversational context is retained.
5. **BreathRoute (`#breathroute`):** Enter starting point and destination. Compare all 7 travel modes side-by-side. Click **"Log Clean Journey"** to instantly generate your **Personal Impact Receipt**.
6. **Life-Switch (`#lifeswitch`):** Select any of the 5 switches. Adjust the slider. See real-time monthly and annual avoided emissions with transparent formulas. Click **"Commit to Switch"** to receive an official receipt.
7. **Impact Tracker & Receipts (`#impact`):** Review your cumulative savings and click **"View Receipt"** on any issued receipt to open the printable modal (`Print / Save as PDF`).
8. **Neighborhood Pulse (`#community`):** Observe genuine aggregated collective metrics and participate in community challenges.
9. **Air-Twin Profile (`#airtwin`):** Inspect your adaptive personal resilience score and safe ventilation windows. Customize your profile or optionally register for cloud sync.
10. **Pollution Explained (`#view-pollution-guide`):** Read the atmospheric science guide explaining PM2.5, PM10, NO₂, O₃, boundary layers, and EPA vs EAQI standards.

---

## 9. LICENSE & ETHICAL COMMITMENT

PRANVYRA is built on open standards and public environmental data for the collective health of urban communities worldwide. Every breath counts. Let's build a cleaner tomorrow together.
