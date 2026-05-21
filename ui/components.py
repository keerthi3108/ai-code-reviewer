"""Reusable Streamlit UI components."""
import html

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer_for_filename, TextLexer

from config import PERSONALITIES, SEVERITY_COLORS, SEVERITY_ORDER
from utils.diff_utils import generate_unified_diff
from utils.scoring import compute_issue_stats, estimate_technical_debt


def render_hero():
    st.markdown("""
    <div class="hero-container">
        <div class="hero-title">🔍 AI Code Review Platform</div>
        <div class="hero-subtitle">
            Enterprise-grade automated reviews • Security scanning • PR-style feedback • Production readiness scores
        </div>
    </div>
    """, unsafe_allow_html=True)


def severity_badge(severity: str) -> str:
    sev = (severity or "info").lower()
    color = SEVERITY_COLORS.get(sev, "#64748b")
    return f'<span class="badge badge-{sev}" style="background:{color}">{sev.upper()}</span>'


def highlight_code(code: str, language: str = "python") -> str:
    if not code.strip():
        return "<pre><code>No code available</code></pre>"
    try:
        lexer = get_lexer_by_name(language, stripall=True)
    except Exception:
        try:
            lexer = guess_lexer_for_filename(f"file.{language}", code)
        except Exception:
            lexer = TextLexer()
    formatter = HtmlFormatter(
        style="monokai",
        noclasses=True,
        cssstyles="font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; background: #0f172a; padding: 1rem; border-radius: 8px; overflow-x: auto;",
    )
    return highlight(code, lexer, formatter)


def render_review_card(issue: dict, index: int):
    sev = issue.get("severity", "info")
    itype = issue.get("type", "issue")
    title = html.escape(issue.get("title", "Issue"))
    message = html.escape(issue.get("message", ""))
    line = issue.get("line", "")
    suggestion = html.escape(issue.get("suggestion", ""))
    source = issue.get("source", "ai")

    st.markdown(f"""
    <div class="review-card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
            <strong style="color:#e2e8f0;">#{index + 1} {title}</strong>
            <div>{severity_badge(sev)} <span style="color:#64748b;font-size:0.75rem;margin-left:0.5rem;">{itype.upper()}</span></div>
        </div>
        <p style="color:#cbd5e1; margin:0.5rem 0;">{message}</p>
        <div style="color:#64748b; font-size:0.8rem;">
            {'Line ' + str(line) + ' • ' if line else ''}{'Source: ' + source}
        </div>
        {f'<p style="color:#86efac; font-size:0.85rem; margin-top:0.5rem;">💡 {suggestion}</p>' if suggestion else ''}
    </div>
    """, unsafe_allow_html=True)


def render_score_pills(scores: dict):
    labels = {
        "readability": "Readability",
        "scalability": "Scalability",
        "production_readiness": "Production Ready",
        "maintainability": "Maintainability",
        "security": "Security",
        "performance": "Performance",
    }
    cols = st.columns(len(labels))
    for col, (key, label) in zip(cols, labels.items()):
        val = scores.get(key, 0)
        color = "#22c55e" if val >= 80 else "#eab308" if val >= 60 else "#ef4444"
        with col:
            st.markdown(f"""
            <div class="score-pill">
                <div class="score-value" style="background:linear-gradient(135deg,{color},{color});-webkit-background-clip:text;">{val}</div>
                <div class="score-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)


def render_radar_chart(scores: dict):
    categories = ["Readability", "Scalability", "Production", "Maintainability", "Security", "Performance"]
    keys = ["readability", "scalability", "production_readiness", "maintainability", "security", "performance"]
    values = [scores.get(k, 50) for k in keys]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill="toself",
        fillcolor="rgba(99, 102, 241, 0.3)",
        line=dict(color="#818cf8", width=2),
        name="Scores",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="#334155", linecolor="#475569"),
            bgcolor="rgba(15, 23, 42, 0.5)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0", family="Inter"),
        height=380,
        margin=dict(l=60, r=60, t=40, b=40),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_severity_chart(issues: list):
    stats = compute_issue_stats(issues)
    df = pd.DataFrame({
        "Severity": [s.capitalize() for s in SEVERITY_ORDER if stats.get(s, 0) > 0],
        "Count": [stats[s] for s in SEVERITY_ORDER if stats.get(s, 0) > 0],
    })
    if df.empty:
        st.info("No issues to chart.")
        return

    colors = [SEVERITY_COLORS.get(s.lower(), "#64748b") for s in df["Severity"].str.lower()]
    fig = go.Figure(go.Bar(
        x=df["Severity"], y=df["Count"],
        marker_color=colors,
        text=df["Count"], textposition="auto",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0"),
        height=300,
        xaxis=dict(gridcolor="#334155"),
        yaxis=dict(gridcolor="#334155"),
        margin=dict(l=40, r=20, t=30, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_inline_comments(comments: list, code: str):
    if not comments:
        st.info("No inline comments generated.")
        return

    lines = code.splitlines()
    for i, c in enumerate(comments):
        line_no = c.get("line", 0)
        sev = c.get("severity", "info")
        comment = html.escape(c.get("comment", ""))
        suggestion = html.escape(c.get("suggestion", ""))
        code_snippet = ""
        if line_no and 0 < line_no <= len(lines):
            code_snippet = html.escape(lines[line_no - 1][:120])

        with st.expander(f"💬 Line {line_no} — {sev.upper()} — {comment[:60]}...", expanded=(i < 2)):
            st.markdown(f"""
            <div class="inline-comment">
                {severity_badge(sev)}
                <p style="color:#e2e8f0; margin:0.5rem 0 0;">{comment}</p>
                {f'<pre class="code-block" style="margin-top:0.5rem;">{code_snippet}</pre>' if code_snippet else ''}
                {f'<p style="color:#86efac;">Suggestion: {suggestion}</p>' if suggestion else ''}
            </div>
            """, unsafe_allow_html=True)


def render_side_by_side(original: str, improved: str, language: str = "python"):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**📄 Original**")
        st.markdown(highlight_code(original, language), unsafe_allow_html=True)
    with col2:
        st.markdown("**✨ Improved**")
        st.markdown(highlight_code(improved or "# No improvements generated", language), unsafe_allow_html=True)


def render_diff_viewer(original: str, improved: str):
    diff_text = generate_unified_diff(original, improved or original)
    st.markdown("**Unified Diff**")
    lines_html = []
    for line in diff_text.splitlines():
        escaped = html.escape(line)
        if line.startswith("+"):
            lines_html.append(f'<div class="diff-add">{escaped}</div>')
        elif line.startswith("-"):
            lines_html.append(f'<div class="diff-remove">{escaped}</div>')
        else:
            lines_html.append(f'<div class="diff-context">{escaped}</div>')
    st.markdown(f'<div class="code-block">{"".join(lines_html)}</div>', unsafe_allow_html=True)


def render_technical_debt(issues: list, scores: dict):
    debt = estimate_technical_debt(issues, scores)
    st.markdown(f"""
    <div class="review-card" style="border-left: 4px solid {debt['color']};">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="color:#94a3b8; font-size:0.8rem;">TECHNICAL DEBT ESTIMATE</div>
                <div style="font-size:1.8rem; font-weight:700; color:#e2e8f0;">{debt['estimated_hours']} hours</div>
            </div>
            <div>
                <span class="badge" style="background:{debt['color']}; color:white;">{debt['priority']} Priority</span>
                <div style="color:#64748b; font-size:0.8rem; margin-top:0.5rem; text-align:right;">{debt['issue_count']} issues</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_personality_selector() -> str:
    st.sidebar.markdown("### 👤 Reviewer Personality")
    keys = list(PERSONALITIES.keys())
    labels = [f"{PERSONALITIES[k]['icon']} {PERSONALITIES[k]['name']}" for k in keys]
    choice = st.sidebar.radio("Select reviewer", labels, label_visibility="collapsed")
    idx = labels.index(choice)
    return keys[idx]


def render_history_card(review: dict):
    created = review.get("created_at", "")[:19].replace("T", " ")
    personality = review.get("personality", "unknown")
    summary = review.get("summary", "")[:120]
    scores = review.get("scores", {})
    prod = scores.get("production_readiness", "—")

    st.markdown(f"""
    <div class="review-card">
        <div style="display:flex; justify-content:space-between;">
            <strong style="color:#e2e8f0;">{review.get('filename', 'Review')} — {review.get('id', '')}</strong>
            <span style="color:#64748b; font-size:0.8rem;">{created}</span>
        </div>
        <p style="color:#94a3b8; font-size:0.85rem;">{personality} • Production: {prod}/100</p>
        <p style="color:#cbd5e1; font-size:0.9rem;">{html.escape(summary)}...</p>
    </div>
    """, unsafe_allow_html=True)
