# Student Learning Behavior Analytics Platform

A full-stack web application that turns raw online course interaction logs into clear, actionable analytics for educators and administrators. Built as a Data Science Seminar II project by **Tasin Jaber**.

---

## What It Does

Instructors and admins can upload a student activity dataset (CSV, Excel, or Google Sheets), then instantly explore:

- How engaged students are over time
- Which students are falling behind and why
- How scores are distributed across the class
- Predicted engagement for the coming week
- AI-generated plain-English summaries of the data

Everything runs in a browser — no data science background needed.

---

## Features

| Category | Feature |
|---|---|
| **Analytics** | Engagement trend chart, activity breakdown, score distribution, active days histogram |
| **Risk Detection** | Automatic at-risk scoring based on low scores, inactivity, and low engagement |
| **Forecasting** | 7-day engagement forecast using linear regression on recent history |
| **Anomaly Detection** | Z-score based spike/drop detection highlighted on the trend chart |
| **AI Insights** | One-click AI summary using Groq (LLaMA 3.3), Google Gemini, or ChatGPT |
| **Student Profiles** | Individual page per student — score trend, activity timeline, risk badge |
| **Comparison View** | Side-by-side comparison of any two students |
| **Activity Heatmap** | GitHub-style calendar showing a full year of daily activity |
| **Multi-Dataset** | Upload CSV/Excel, paste a Google Sheets URL, or use the default Kaggle dataset |
| **Export** | Download filtered data as CSV, Excel, or PDF report |
| **User Management** | Admin panel to create, edit, reset passwords, and delete users |
| **Registration Flow** | Users can request access; admin approves or declines from one table |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, React Router v6, Recharts, Axios |
| Backend | FastAPI (Python), Motor (async MongoDB driver) |
| Database | MongoDB Atlas (cloud) |
| AI | Groq API (LLaMA 3.3), Google Gemini, OpenAI GPT-4o-mini |
| Data | Pandas (CSV/Excel ingestion), NumPy (forecasting) |
| Auth | Bearer token, role-based access (admin) |
| Build | Vite, uvicorn |

---

## Project Structure

```
project 2/
├── backend/
│   ├── main.py                        # FastAPI app entry point
│   ├── requirements.txt
│   ├── .env                           # API keys (not committed)
│   └── app/
│       ├── api/
│       │   ├── routes.py              # Analytics endpoints
│       │   ├── auth_routes.py         # Auth & user management endpoints
│       │   └── dataset_routes.py      # Dataset upload/manage endpoints
│       ├── services/
│       │   ├── analytics.py           # Core analytics logic
│       │   ├── dataset_manager.py     # CSV/Excel/URL ingestion
│       │   ├── ml_analytics.py        # Forecasting & anomaly detection
│       │   └── ai_insights.py         # AI provider integration
│       ├── auth.py                    # Auth logic, token store, user CRUD
│       ├── db.py                      # MongoDB connection
│       └── config.py
└── frontend/
    ├── public/
    │   └── logo.png
    ├── src/
    │   ├── pages/
    │   │   ├── LandingPage.jsx
    │   │   ├── LoginPage.jsx          # Standalone auth page (sign in + register)
    │   │   ├── DashboardPage.jsx      # Main analytics dashboard
    │   │   ├── StudentProfilePage.jsx
    │   │   ├── ComparisonPage.jsx
    │   │   └── AdminPage.jsx          # User management panel
    │   ├── components/
    │   │   ├── SidebarLayout.jsx
    │   │   ├── MetricCard.jsx
    │   │   ├── HeatmapCalendar.jsx
    │   │   ├── DatasetManager.jsx
    │   │   └── InfoTip.jsx
    │   ├── services/
    │   │   └── analyticsApi.js        # All API calls
    │   ├── App.jsx
    │   └── styles.css
    ├── package.json
    └── vite.config.js
```

---

## Setup & Run

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB Atlas account (free tier works)

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Create a `.env` file in `backend/`:

```env
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/<db>
GROQ_API_KEY=your_groq_key
GOOGLE_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
```

Start the server:

```bash
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

### Default login

| Username | Password |
|---|---|
| `admin` | `admin123` |

---

## API Overview

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/login` | Get bearer token |
| POST | `/auth/register` | Submit registration request |
| GET | `/auth/me` | Current user info |
| GET | `/auth/admin-data` | All users + requests in one call (admin) |
| POST | `/auth/users` | Create user (admin) |
| PUT | `/auth/users/{username}` | Edit role or password (admin) |
| DELETE | `/auth/users/{username}` | Delete user (admin) |
| POST | `/auth/registration-requests/{id}/approve` | Approve request (admin) |
| POST | `/auth/registration-requests/{id}/decline` | Decline request (admin) |

### Analytics
| Method | Endpoint | Description |
|---|---|---|
| GET | `/analytics/overview` | Summary metrics |
| GET | `/analytics/engagement-trend` | Daily/monthly interaction counts |
| GET | `/analytics/activity-breakdown` | Event type distribution |
| GET | `/analytics/score-distribution` | Score range histogram |
| GET | `/analytics/at-risk-students` | At-risk list (admin only) |
| GET | `/analytics/forecast` | 7-day engagement prediction |
| GET | `/analytics/anomalies` | Spike/drop detection |
| GET | `/analytics/heatmap` | Year-long daily activity data |
| GET | `/analytics/student/{id}` | Individual student details |
| GET | `/analytics/compare` | Side-by-side student comparison |
| GET | `/analytics/ai-insights` | AI-generated summary |
| GET | `/analytics/export` | CSV or Excel download |

### Datasets
| Method | Endpoint | Description |
|---|---|---|
| GET | `/datasets/` | List all uploaded datasets |
| POST | `/datasets/upload` | Upload CSV or Excel file |
| POST | `/datasets/from-url` | Import from Google Sheets URL |
| GET | `/datasets/{id}/validate` | Check field compatibility |
| DELETE | `/datasets/{id}` | Remove dataset |

---

## Dataset Compatibility

The platform works with two types of data:

**Event log format** — one row per activity event:
```
user_id, timestamp, course, event_type, score, duration
```

**Open edX person-course format** — one row per student enrollment (Kaggle):
```
user_id, course_id, nevents, ndays_act, nplay_video, nchapters, grade, certified
```

Upload either format and the dashboard automatically adapts its charts and labels.

---

## How the Risk Score Works

Each student gets a risk score from 0 to 1 based on three factors:

1. **Low average score** — below the class median
2. **Long inactivity** — days since last activity, normalized by the dataset range
3. **Low total engagement** — total events below the class median

The three scores are averaged. Students above 0.5 are flagged as at-risk.

---

## How Forecasting Works

The backend takes the last 30 days of daily interaction counts and fits a linear trend using NumPy's `polyfit`. It then projects forward 7 days and reports whether the overall trend is rising, falling, or stable.

---

## Notes

- The backend returns mock/fallback data if MongoDB is unreachable, so the dashboard always renders.
- API keys are loaded from `.env` and never exposed to the frontend.
- The `TOKEN_STORE` in `auth.py` is in-memory — tokens are lost on backend restart (by design for this project scope).
