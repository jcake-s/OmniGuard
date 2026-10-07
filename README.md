# 🛡️ OmniGuard

**AI-Powered Financial Sentinel & Personalized Wealth Advisory Platform**  
*Built for the Banking & Financial Services Sector with a 100% Free Technology Stack*

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🌟 Key Features

1. **⚡ Real-Time Fraud & Anomaly Sentinel**:
   - Scores transactions from **0 to 100** with risk levels (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
   - Detects impossible travel geodistance velocity, sudden offshore wires, and rapid ATM bursts.
   - Explainable AI (XAI) output provides clear reasons and prescribed actions (`APPROVE`, `REQUIRE_2FA`, `FLAG_FOR_REVIEW`, `BLOCK`).

2. **💡 Wealth & Budget Copilot**:
   - Leverages **Gemini 3 Flash**'s long-context window to evaluate 30–90 day transaction histories.
   - Computes a dynamic **Financial Health Index (0–100)**.
   - Analyzes category spend outflows to prescribe realistic monthly budget ceilings.
   - Conversational AI Copilot to answer queries on savings, emergency reserves, and audit flags.

3. **📋 Transaction Ledger & Regulatory Triage**:
   - Paginated, searchable, and filterable transaction ledger.
   - Compliance triage interface to resolve alerts (`CONFIRMED_FRAUD`, `FALSE_POSITIVE`, `RESOLVED`).
   - One-click CSV export for audit records.

4. **🔒 Bank-Grade Privacy & Security**:
   - PII Scrubbing pipeline automatically masks card PANs (`****-****-****-1234`), SSNs, emails, and phone numbers before AI calls.
   - Supabase Row-Level Security (RLS) ensures multi-tenant data isolation.

5. **💸 100% Free Technology Stack**:
   - **Frontend & App Server**: Streamlit Community Cloud (Free)
   - **Database**: Supabase PostgreSQL Free Tier (Free)
   - **AI Inference**: Google AI Studio Gemini Flash Free Tier (15 RPM) (Free)
   - **Hosting & CI/CD**: GitHub + Streamlit Cloud (Free)

---

## 🏗️ Architecture & Project Structure

```
omniguard/
├── .streamlit/
│   ├── config.toml           # Theme configuration (Fintech Dark Mode)
│   └── secrets.toml.example  # Secrets template
├── app.py                    # Streamlit Application Entrypoint
├── requirements.txt          # Python dependencies
├── README.md                 # Project Documentation
├── services/
│   ├── __init__.py
│   ├── db_service.py         # Supabase PostgreSQL + Demo Store Layer
│   ├── gemini_client.py      # Google AI Studio Gemini Flash Service
│   ├── fraud_engine.py       # Fraud Detection & Batch Ingestion
│   └── advisory_engine.py    # Wealth Planning & Copilot Logic
├── utils/
│   ├── __init__.py
│   ├── masking.py            # PII Sanitization & Regex Masking
│   └── mock_data.py          # Realistic Banking Data & Anomaly Generator
└── tests/
    └── test_omniguard.py     # Unit & Integration Test Suite
```

---

## 🚀 Quickstart Guide

### 1. Clone & Set Active Workspace
```bash
git clone <your-repo-url>
cd omniguard
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application (Immediate Demo Mode)
The app runs out-of-the-box with a high-fidelity in-memory demo database and intelligent simulation even before adding API keys:
```bash
python -m streamlit run app.py
```
*Or simply execute the launcher script:*
```powershell
.\run.ps1
# or run.bat
```

### 4. Configure Production Credentials (Optional)
Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`:
```toml
# Google AI Studio Gemini API Key (https://aistudio.google.com)
GEMINI_API_KEY = "AIzaSy..."

# Model Selection
GEMINI_MODEL = "gemini-3-flash"

# Supabase Credentials (https://supabase.com)
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "eyJhbGciOi..."
```

---

## ☁️ Free Deployment to Streamlit Community Cloud

1. Push your repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io).
3. Connect your repository, branch (`main`), and set file path to `app.py`.
4. Under **Advanced settings > Secrets**, paste your production keys.
5. Click **Deploy!**
