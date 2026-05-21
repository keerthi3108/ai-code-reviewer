"""
AI Automated Code Reviewer — Enterprise Streamlit Application
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import PERSONALITIES, SUPPORTED_EXTENSIONS
from services.ai_reviewer import get_api_status, review_code
from services.bandit_scanner import get_python_code, run_bandit_scan, should_run_bandit
from services.storage import ReviewStorage
from ui.components import (
    highlight_code,
    render_diff_viewer,
    render_hero,
    render_history_card,
    render_inline_comments,
    render_personality_selector,
    render_radar_chart,
    render_review_card,
    render_score_pills,
    render_severity_chart,
    render_side_by_side,
    render_technical_debt,
)
from ui.styles import inject_styles
from utils.file_handler import aggregate_code, detect_language, primary_language, process_uploaded_file
from utils.scoring import compute_issue_stats

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Code Reviewer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_styles()

# ─── Session state ───────────────────────────────────────────────────────────
if "review_result" not in st.session_state:
    st.session_state.review_result = None
if "original_code" not in st.session_state:
    st.session_state.original_code = ""
if "files_meta" not in st.session_state:
    st.session_state.files_meta = []
if "storage" not in st.session_state:
    st.session_state.storage = ReviewStorage()


def run_full_review(code: str, files: list, personality: str, filename: str):
    """Execute AI review + Bandit scan and store results."""
    language = primary_language(files) if files else detect_language(filename)

    with st.spinner("🤖 AI reviewer analyzing your code..."):
        ai_result = review_code(code, language, personality, filename)

    bandit_issues = []
    if should_run_bandit(files if files else [{"language": language, "path": filename}]):
        py_code = get_python_code(files) if files else (code if language == "python" else None)
        if py_code:
            with st.spinner("🛡️ Running Bandit security scan..."):
                bandit = run_bandit_scan(py_code, "review.py")
                bandit_issues = bandit.get("issues", [])
                if bandit.get("skipped") and bandit.get("reason"):
                    st.sidebar.warning(f"Bandit: {bandit['reason']}")

    all_issues = (ai_result.get("issues") or []) + bandit_issues
    ai_result["issues"] = all_issues
    ai_result["bandit_count"] = len(bandit_issues)
    ai_result["language"] = language
    ai_result["personality"] = PERSONALITIES[personality]["name"]
    ai_result["filename"] = filename
    ai_result["reviewed_at"] = datetime.now(timezone.utc).isoformat()

    st.session_state.review_result = ai_result
    st.session_state.original_code = code
    st.session_state.files_meta = files

    # Persist to TinyDB
    save_data = {k: v for k, v in ai_result.items() if k != "original_code"}
    save_data["code_preview"] = code[:2000]
    review_id = st.session_state.storage.save_review(save_data)
    ai_result["saved_id"] = review_id

    return ai_result


def sidebar_config():
    st.sidebar.markdown("## ⚙️ Configuration")
    api = get_api_status()

    if api["ready"]:
        provider = "Groq" if api["groq"] and (api["provider"] == "groq" or not api["openai"]) else "OpenAI"
        st.sidebar.success(f"✅ {provider} API connected")
    else:
        st.sidebar.error("❌ No API key — using offline heuristics")
        st.sidebar.info("Add GROQ_API_KEY or OPENAI_API_KEY to `.env`")

    personality = render_personality_selector()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Quick Stats")
    if st.session_state.review_result:
        r = st.session_state.review_result
        stats = compute_issue_stats(r.get("issues", []))
        st.sidebar.metric("Total Issues", len(r.get("issues", [])))
        st.sidebar.metric("Bandit Findings", r.get("bandit_count", 0))
        st.sidebar.metric("Production Score", r.get("scores", {}).get("production_readiness", "—"))
    else:
        st.sidebar.info("Run a review to see stats")

    st.sidebar.markdown("---")
    page = st.sidebar.radio(
        "Navigation",
        ["🔍 New Review", "📋 Review Results", "📜 History", "ℹ️ About"],
        label_visibility="collapsed",
    )
    return personality, page


def page_new_review(personality: str):
    st.markdown("### Submit Code for Review")

    input_tab, upload_tab, zip_tab = st.tabs(["📝 Paste Code", "📁 Upload File", "📦 Upload ZIP Project"])

    code = ""
    files = []
    filename = "pasted_code.py"

    with input_tab:
        lang_choice = st.selectbox(
            "Language",
            ["python", "javascript", "typescript", "java", "go", "rust", "cpp", "csharp", "ruby", "php", "sql", "other"],
        )
        code = st.text_area(
            "Paste your code here",
            height=320,
            placeholder="# Paste code here...\ndef hello():\n    print('world')",
        )
        filename = f"pasted_code.{lang_choice if lang_choice != 'other' else 'txt'}"
        if code.strip():
            files = [{"path": filename, "content": code, "language": lang_choice}]

    with upload_tab:
        uploaded = st.file_uploader(
            "Upload a source file",
            type=[ext.lstrip(".") for ext in SUPPORTED_EXTENSIONS],
        )
        if uploaded:
            result = process_uploaded_file(uploaded)
            if result:
                files = result["files"]
                code, files = aggregate_code(files)
                filename = files[0]["path"] if files else uploaded.name
                st.success(f"Loaded: {filename}")
                st.code(code[:1500] + ("..." if len(code) > 1500 else ""), language=files[0].get("language", "python"))

    with zip_tab:
        zip_file = st.file_uploader("Upload ZIP project", type=["zip"])
        if zip_file:
            result = process_uploaded_file(zip_file)
            if result and result.get("files"):
                files = result["files"]
                code, files = aggregate_code(files)
                filename = f"{zip_file.name} ({len(files)} files)"
                st.success(f"Extracted {len(files)} files from ZIP")
                with st.expander("View extracted files"):
                    for f in files:
                        st.text(f"• {f['path']} ({f['language']})")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        review_btn = st.button("🚀 Run AI Code Review", type="primary", use_container_width=True)
    with col2:
        st.caption(f"Reviewer: {PERSONALITIES[personality]['icon']} {PERSONALITIES[personality]['name']}")
    with col3:
        clear_btn = st.button("🗑️ Clear", use_container_width=True)

    if clear_btn:
        st.session_state.review_result = None
        st.session_state.original_code = ""
        st.rerun()

    if review_btn:
        if not code.strip():
            st.error("Please paste or upload code before running a review.")
        else:
            run_full_review(code, files, personality, filename)
            st.success("Review complete! Open **Review Results** in the sidebar.")
            st.balloons()


def page_review_results():
    result = st.session_state.review_result
    if not result:
        st.info("No review yet. Go to **New Review** and submit code.")
        return

    if result.get("_fallback"):
        st.warning("Running in offline/heuristic mode. Add API keys for full AI analysis.")

    st.markdown(f"### Review: {result.get('filename', 'Code')}")
    st.markdown(f"*{result.get('personality', '')} • {result.get('reviewed_at', '')[:19]}*")

    # Summary card
    st.markdown(f"""
    <div class="review-card" style="border-left: 4px solid #6366f1;">
        <div style="color:#94a3b8; font-size:0.8rem; margin-bottom:0.25rem;">EXECUTIVE SUMMARY</div>
        <p style="color:#e2e8f0; font-size:1rem; margin:0;">{result.get('summary', '')}</p>
    </div>
    """, unsafe_allow_html=True)

    render_score_pills(result.get("scores", {}))

    tab_overview, tab_issues, tab_comments, tab_fixes, tab_compare, tab_security, tab_export = st.tabs([
        "📊 Overview",
        "🐛 Issues",
        "💬 PR Comments",
        "🔧 Fixes & Code",
        "↔️ Compare",
        "🛡️ Security",
        "📥 Export",
    ])

    issues = result.get("issues", [])
    scores = result.get("scores", {})
    original = st.session_state.original_code
    language = result.get("language", "python")

    with tab_overview:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("#### Quality Radar")
            render_radar_chart(scores)
        with c2:
            st.markdown("#### Issue Severity Distribution")
            render_severity_chart(issues)

        render_technical_debt(issues, scores)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### ✅ Strengths")
            for s in result.get("strengths", []):
                st.markdown(f"- {s}")
        with col_b:
            st.markdown("#### 📌 Recommendations")
            for r in result.get("recommendations", []):
                st.markdown(f"- {r}")

    with tab_issues:
        st.markdown(f"**{len(issues)} issues found** ({result.get('bandit_count', 0)} from Bandit)")
        filter_sev = st.multiselect(
            "Filter by severity",
            ["critical", "high", "medium", "low", "info"],
            default=["critical", "high", "medium", "low", "info"],
        )
        filter_type = st.multiselect(
            "Filter by type",
            list({i.get("type", "other") for i in issues}) or ["bug"],
            default=list({i.get("type", "other") for i in issues}),
        )
        filtered = [
            i for i in issues
            if i.get("severity", "info") in filter_sev
            and i.get("type", "other") in filter_type
        ]
        for idx, issue in enumerate(filtered):
            render_review_card(issue, idx)

    with tab_comments:
        render_inline_comments(result.get("inline_comments", []), original)

    with tab_fixes:
        st.markdown("#### 🛠️ Recommended Fixes")
        for i, fix in enumerate(result.get("fixes", []), 1):
            st.markdown(f"{i}. {fix}")

        opt = result.get("optimized_code", "")
        ref = result.get("refactored_code", "")

        if opt:
            st.markdown("#### ⚡ Optimized Code")
            st.markdown(highlight_code(opt, language), unsafe_allow_html=True)
        if ref:
            st.markdown("#### 🏗️ Refactored Code")
            st.markdown(highlight_code(ref, language), unsafe_allow_html=True)
        if not opt and not ref:
            st.info("No optimized/refactored code generated. Issues and fixes are still available above.")

    with tab_compare:
        improved = result.get("optimized_code") or result.get("refactored_code") or ""
        sub1, sub2, sub3 = st.tabs(["Side by Side", "Diff View", "Original Only"])
        with sub1:
            render_side_by_side(original, improved, language)
        with sub2:
            render_diff_viewer(original, improved)
        with sub3:
            st.markdown(highlight_code(original, language), unsafe_allow_html=True)

    with tab_security:
        sec_issues = [i for i in issues if i.get("type") == "security" or i.get("source") == "bandit"]
        st.markdown(f"**{len(sec_issues)} security findings**")
        if sec_issues:
            for idx, issue in enumerate(sec_issues):
                render_review_card(issue, idx)
        else:
            st.success("No security vulnerabilities detected by AI or Bandit.")
        st.markdown("#### Security Score")
        st.progress(scores.get("security", 0) / 100)
        st.caption(f"Security score: {scores.get('security', 0)}/100")

    with tab_export:
        export = {k: v for k, v in result.items() if not k.startswith("_")}
        st.download_button(
            "📥 Download JSON Report",
            data=json.dumps(export, indent=2, default=str),
            file_name=f"review_{result.get('saved_id', 'report')}.json",
            mime="application/json",
        )
        if st.button("Copy summary to clipboard"):
            st.code(result.get("summary", ""))


def page_history():
    st.markdown("### 📜 Review History")
    storage = st.session_state.storage

    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("Search reviews", placeholder="filename, personality, summary...")
    with col2:
        if st.button("🗑️ Clear All History", type="secondary"):
            n = storage.clear_all()
            st.warning(f"Cleared {n} reviews.")
            st.rerun()

    reviews = storage.search(search) if search else storage.get_all()

    if not reviews:
        st.info("No saved reviews yet.")
        return

    for review in reviews:
        render_history_card(review)
        if st.button(f"Load review {review.get('id')}", key=f"load_{review.get('id')}"):
            st.session_state.review_result = review
            st.session_state.original_code = review.get("code_preview", "")
            st.success("Review loaded. Open **Review Results**.")
            st.rerun()


def page_about():
    st.markdown("""
    ### About AI Code Review Platform

    An enterprise-style automated code reviewer built with **Python** and **Streamlit**.

    **Features**
    - AI-powered analysis (Groq / OpenAI)
    - Bandit security scanning for Python
    - Reviewer personalities: Friendly Mentor, Strict Senior, Startup CTO, FAANG Reviewer
    - PR-style inline comments, severity badges, radar & bar charts
    - Side-by-side code comparison with syntax highlighting (Pygments)
    - Technical debt estimation and production readiness scores
    - Review history via TinyDB (JSON storage)

    **Setup**
    ```bash
    pip install -r requirements.txt
    cp .env.example .env
    # Add GROQ_API_KEY or OPENAI_API_KEY
    streamlit run app.py
    ```
    """)


def main():
    render_hero()
    personality, page = sidebar_config()

    if page == "🔍 New Review":
        page_new_review(personality)
    elif page == "📋 Review Results":
        page_review_results()
    elif page == "📜 History":
        page_history()
    else:
        page_about()


if __name__ == "__main__":
    main()
