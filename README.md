# 🤖 SmartAI Agent Chatbot

A high-performance, full-stack AI application designed to analyze GitHub repositories, extract developer skills, match them against industry trends, and generate personalized 8–12 week learning roadmaps using Google Gemini 2.0 Flash.

---

## 🚀 Core Features

### 1. Multi-turn AI Chat
- Natural language interaction with **Gemini 2.0 Flash**.
- Remembers context and previous turns for a seamless experience.

### 2. Deep GitHub Repository Analysis
- Analyzes repository metadata: languages, commit frequency, repository size, license, and structure.
- **README Intelligence**: Summarizes the project's purpose and key features using AI.
- **Tech Stack Detection**: Identifies frameworks, libraries, and tools (e.g., FastAPI, React, Docker, TensorFlow).

### 3. Skill Extraction & Scoring
- Maps raw repository data to a comprehensive **Developer Skill Profile**.
- Calculates a **Skill Score (0–100)** based on:
    - **Breadth**: Total number of unique skills discovered.
    - **Market Relevance**: How many skills match top industry trends.
    - **Depth Bonus**: Logarithmic bonus for advanced repository indicators (commit count, stars/forks).

### 4. Market Trend Matching
- Compares user skills against 8 key industry domains:
    - AI / Machine Learning Engineer
    - Full Stack Web Developer
    - Cloud / DevOps Engineer
    - Mobile App Developer
    - Data Engineer
    - Backend / API Developer
    - Web3 / Blockchain Developer
    - Game Developer
- Identifies **Matched Skills**, **Missing Skills**, and **Alternative Career Paths**.

### 5. AI-Powered Learning Roadmap
- Generates a **personalized 8–12 week roadmap** based on missing skills and a target career goal.
- Includes **weekly focus**, **specific learning items**, **hands-on projects**, and **curated resources** (docs, courses, tools).

---

## 🛠️ Technical Stack

- **Backend**: FastAPI (Python), `google-genai` SDK, `pydantic`, `httpx`.
- **Frontend**: React (Vite), Axios, `marked` (Markdown rendering).
- **Styling**: Vanilla CSS with a **modern glassmorphism** aesthetic.
- **AI**: Google Gemini 2.0 Flash.
- **API**: GitHub REST API.

---

## 📂 Project Structure

```text
SmartAi agent chatbot/
├── backend/
│   ├── main.py              # FastAPI Entry Point
│   ├── config.py            # Environment Configuration
│   ├── routes/              # API Endpoints (chat, github, analyze)
│   ├── services/            # Core Logic (Gemini, GitHub, Trends, Pipeline)
│   ├── models/              # Pydantic Schemas
│   └── requirements.txt     # Python Dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Main UI Entry Point (3-panel layout)
│   │   ├── components/       # UI Components (Sidebar, Chat, AnalysisPanel)
│   │   ├── hooks/            # Custom Hooks (useChat)
│   │   └── services/         # API Client (api.js)
│   └── index.css             # Global Styles & Design System
└── README.md                 # This documentation
```

---

## 📈 The Pipeline Logic

The **Full Analysis Pipeline** (`POST /analyze`) follows a 4-step sequential flow:

1.  **Ingest**: Fetches raw data from GitHub (languages, README, stats).
2.  **Extract**: Analyzes the data to build a Skill Profile.
3.  **Match**: Compares the profile against market trend requirements.
4.  **Generate**: Sends the delta (missing skills) + target goal to Gemini to build a structured curriculum.

---

## ⚙️ Setup & Installation

### 1. Backend Setup
1.  Navigate to `backend/`.
2.  Create a Virtual Environment: `python -m venv venv`.
3.  Activate it: `.\venv\Scripts\activate` (Windows).
4.  Install dependencies: `pip install -r requirements.txt`.
5.  Create a `.env` file with:
    ```env
    GEMINI_API_KEY=your_key_here
    GITHUB_TOKEN=your_token_here
    ```
6.  Start the server: `python -m uvicorn main:app --reload`.

### 2. Frontend Setup
1.  Navigate to `frontend/`.
2.  Install packages: `npm install`.
3.  Start the dev server: `npm run dev`.

---

## 🛣️ Roadmap for Future Versions
- [ ] **Authentication**: User accounts to save roadmaps.
- [ ] **Data Persistence**: Store analysis results in a database (e.g., PostgreSQL).
- [ ] **Multi-Repo Profiling**: Analyze an entire GitHub profile for a full career overview.
- [ ] **Progress Tracking**: Interactive checkboxes in the Roadmap timeline.
