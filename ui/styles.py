"""Enterprise UI styles for Streamlit."""
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
}

.main .block-container {
    padding-top: 1.5rem;
    max-width: 1400px;
}

/* Hero header */
.hero-container {
    background: linear-gradient(135deg, #1e40af 0%, #7c3aed 50%, #db2777 100%);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 20px 60px rgba(30, 64, 175, 0.3);
    animation: fadeInDown 0.6s ease-out;
}

.hero-title {
    font-size: 2.2rem;
    font-weight: 700;
    color: white;
    margin: 0;
    letter-spacing: -0.02em;
}

.hero-subtitle {
    color: rgba(255,255,255,0.85);
    font-size: 1rem;
    margin-top: 0.5rem;
}

/* Review cards */
.review-card {
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(148, 163, 184, 0.15);
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    backdrop-filter: blur(10px);
    transition: transform 0.2s, box-shadow 0.2s;
    animation: fadeInUp 0.4s ease-out;
}

.review-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.3);
    border-color: rgba(99, 102, 241, 0.4);
}

/* Severity badges */
.badge {
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 9999px;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.badge-critical { background: #dc2626; color: white; }
.badge-high { background: #ea580c; color: white; }
.badge-medium { background: #ca8a04; color: #1e293b; }
.badge-low { background: #2563eb; color: white; }
.badge-info { background: #64748b; color: white; }

/* Score pills */
.score-pill {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 10px;
    padding: 0.75rem 1rem;
    text-align: center;
    animation: fadeIn 0.5s ease-out;
}

.score-value {
    font-size: 1.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.score-label {
    font-size: 0.75rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* Inline comment */
.inline-comment {
    background: rgba(15, 23, 42, 0.5);
    border-left: 3px solid #6366f1;
    padding: 0.75rem 1rem;
    margin: 0.5rem 0;
    border-radius: 0 8px 8px 0;
    font-size: 0.9rem;
}

/* Diff viewer */
.diff-add { background: rgba(34, 197, 94, 0.15); color: #4ade80; }
.diff-remove { background: rgba(239, 68, 68, 0.15); color: #f87171; }
.diff-context { color: #94a3b8; }

/* Syntax block */
.code-block {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 1rem;
    overflow-x: auto;
    line-height: 1.5;
}

/* Metric strip */
.metric-strip {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    margin: 1rem 0;
}

/* Personality card */
.personality-active {
    border: 2px solid #6366f1 !important;
    background: rgba(99, 102, 241, 0.15) !important;
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-12px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

.scanning-pulse {
    animation: pulse 1.5s ease-in-out infinite;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
}

section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #e2e8f0;
}

/* Hide streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Responsive */
@media (max-width: 768px) {
    .hero-title { font-size: 1.5rem; }
    .hero-container { padding: 1.25rem; }
}
</style>
"""


def inject_styles():
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
