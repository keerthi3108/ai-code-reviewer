# AI Automated Code Reviewer

Enterprise-style AI-powered code review platform built with **Python** and **Streamlit**. Paste code, upload files, or drop a ZIP project — get PR-style feedback, security scans, scores, and refactored code.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red)

## Features

- **AI Code Review** — Groq (Llama 3.3 70B) or OpenAI GPT-4o-mini
- **Reviewer Personalities** — Friendly Mentor, Strict Senior Engineer, Startup CTO, FAANG Reviewer
- **Security Scanning** — Bandit for Python vulnerabilities
- **Rich UI** — Review cards, severity badges, radar charts, diff viewer, collapsible PR comments, syntax highlighting
- **Scores** — Readability, scalability, production readiness, maintainability, security, performance
- **Technical Debt** — Estimated remediation hours
- **Code Comparison** — Side-by-side original vs improved + unified diff
- **History** — TinyDB JSON persistence (no SQL)

## Quick Start

```bash
cd "Automated Code Reviewer"
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env         # Add your API keys
streamlit run app.py
```

Open **http://localhost:8501**

## API Keys

**Local:** create a `.env` file:

```env
GROQ_API_KEY=gsk_...          # https://console.groq.com
OPENAI_API_KEY=sk-...         # https://platform.openai.com (optional)
AI_PROVIDER=groq              # groq | openai
```

**Streamlit Cloud (after deploy):** open your app → **Settings** → **Secrets** and paste:

```toml
GROQ_API_KEY = "gsk_..."
OPENAI_API_KEY = "sk-..."
AI_PROVIDER = "groq"
```

Save secrets and **Reboot app**. Keys are not stored in your repo.

**Local Streamlit secrets:** copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` (gitignored).

Without API keys, the app runs in **offline heuristic mode** (pattern-based checks).

## Usage

1. Choose a **reviewer personality** in the sidebar
2. Paste code, upload a file, or upload a **ZIP project**
3. Click **Run AI Code Review**
4. Explore tabs: Overview, Issues, PR Comments, Fixes, Compare, Security, Export
5. View past reviews under **History**

## Project Structure

```
├── app.py                 # Main Streamlit application
├── config.py              # Settings & personalities
├── requirements.txt
├── services/
│   ├── ai_reviewer.py     # Groq/OpenAI integration
│   ├── bandit_scanner.py  # Security scanning
│   └── storage.py         # TinyDB review history
├── ui/
│   ├── components.py      # Cards, charts, diff viewer
│   └── styles.py          # Enterprise CSS theme
└── utils/
    ├── file_handler.py    # ZIP/file processing
    ├── diff_utils.py      # Diff generation
    └── scoring.py         # Debt & stats
```

## Tech Stack

| Component | Library |
|-----------|---------|
| UI | Streamlit |
| AI | Groq / OpenAI |
| Security | Bandit |
| Syntax | Pygments |
| Charts | Plotly |
| Storage | TinyDB |

## License

MIT
