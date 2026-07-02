from utils.gemini_helper_new import (
    parse_resume_and_score, match_jd, generate_interview_questions,
    rewrite_bullets, generate_cover_letter
)
from utils.pdf_parser import extract_text
from utils.pdf_report import generate_pdf_report

import streamlit as st
import plotly.graph_objects as go

# ═══════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════
st.set_page_config(
    page_title="SmartResume AI",
    page_icon="📄",
    layout="wide"
)

# ═══════════════════════════════════════════════════
# CUSTOM CSS
# ═══════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"] {
    background-color: #F7F9FC !important;
    color-scheme: light !important;
    font-family: 'Inter', sans-serif !important;
}

.main, .main .block-container {
    background-color: #F7F9FC !important;
    color: #2C3E50 !important;
    max-width: 1200px !important;
    padding-top: 1.5rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    padding-bottom: 4rem !important;
    font-family: 'Inter', sans-serif !important;
}

.main *:not(svg):not(path) {
    color: #2C3E50 !important;
    font-family: 'Inter', sans-serif !important;
}

[data-testid="stHeader"] {
    background-color: #F7F9FC !important;
}
[data-testid="stHeader"] *:not(svg):not(path) { color: #2C3E50 !important; }
[data-testid="stToolbar"] button,
[data-testid="stToolbar"] span,
button[kind="header"],
[data-testid="stStatusWidget"] *:not(svg):not(path),
[data-testid="stMainMenu"] *:not(svg):not(path) { color: #2C3E50 !important; }
[data-testid="stToolbar"] svg,
[data-testid="stMainMenu"] svg,
[data-testid="stStatusWidget"] svg { fill: #2C3E50 !important; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1E3A5F 0%, #162D4A 100%) !important;
    border-right: 1px solid #2E4F6F !important;
}
[data-testid="stSidebar"] *:not(svg):not(path) {
    color: #E8F0FE !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stSidebar"] .stRadio > label { display: none; }
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] { gap: 4px; }
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
    background: rgba(255,255,255,0.06) !important;
    border-radius: 10px !important;
    padding: 10px 16px !important;
    margin: 3px 0 !important;
    cursor: pointer !important;
    transition: all 0.2s !important;
    border: 1px solid transparent !important;
    display: flex !important;
    align-items: center !important;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {
    background: rgba(255,255,255,0.12) !important;
    border-color: rgba(46,134,171,0.4) !important;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[data-checked="true"],
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[aria-checked="true"] {
    background: rgba(46,134,171,0.25) !important;
    border-color: #2E86AB !important;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label p {
    font-size: 14px !important;
    font-weight: 500 !important;
}

.hero-container {
    background: linear-gradient(135deg, #1E3A5F 0%, #2E86AB 100%);
    border-radius: 20px;
    padding: 52px 48px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
}
.hero-container::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 280px; height: 280px;
    background: rgba(255,255,255,0.05);
    border-radius: 50%;
}
.hero-container::after {
    content: '';
    position: absolute;
    bottom: -80px; left: -40px;
    width: 220px; height: 220px;
    background: rgba(255,255,255,0.04);
    border-radius: 50%;
}
.hero-title {
    font-size: 42px;
    font-weight: 800;
    color: white !important;
    line-height: 1.2;
    margin-bottom: 14px;
}
.hero-subtitle {
    font-size: 17px;
    color: rgba(255,255,255,0.82) !important;
    line-height: 1.6;
    max-width: 600px;
    margin-bottom: 28px;
}
.hero-badge {
    display: inline-block;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.3);
    color: white !important;
    border-radius: 30px;
    padding: 6px 16px;
    font-size: 13px;
    font-weight: 600;
    margin-right: 10px;
    margin-bottom: 8px;
    backdrop-filter: blur(10px);
}

.features-row {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 14px;
    margin-bottom: 32px;
}
.feature-card {
    background: white;
    border-radius: 14px;
    padding: 20px 16px;
    text-align: center;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    border: 1px solid #E8EDF5;
    transition: all 0.2s;
    cursor: default;
}
.feature-card:hover {
    box-shadow: 0 6px 24px rgba(46,134,171,0.18);
    border-color: #2E86AB;
    transform: translateY(-3px);
}
.feature-icon { font-size: 28px; margin-bottom: 10px; display: block; }
.feature-title { font-size: 13px; font-weight: 700; color: #1E3A5F !important; margin-bottom: 5px; }
.feature-desc { font-size: 11px; color: #7F8C8D !important; line-height: 1.5; }

.steps-row {
    display: flex;
    align-items: center;
    gap: 0;
    margin-bottom: 28px;
    background: white;
    border-radius: 14px;
    padding: 20px 28px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    border: 1px solid #E8EDF5;
}
.step-item { display: flex; align-items: center; gap: 12px; flex: 1; }
.step-number {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, #1E3A5F, #2E86AB);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    color: white !important; font-size: 15px; font-weight: 700; flex-shrink: 0;
}
.step-text-title { font-size: 13px; font-weight: 700; color: #1E3A5F !important; }
.step-text-sub { font-size: 11px; color: #7F8C8D !important; }
.step-arrow { color: #BDC3CC !important; font-size: 22px; margin: 0 8px; flex-shrink: 0; }

.upload-label { font-size: 16px; font-weight: 700; color: #1E3A5F !important; margin-bottom: 6px; }
.upload-hint { font-size: 13px; color: #7F8C8D !important; margin-bottom: 16px; }

.sidebar-logo { text-align: center; padding: 20px 0 8px 0; }
.sidebar-logo-icon { font-size: 36px; display: block; margin-bottom: 6px; }
.sidebar-logo-text { font-size: 18px !important; font-weight: 800 !important; color: white !important; letter-spacing: -0.3px; }
.sidebar-logo-sub { font-size: 11px !important; color: rgba(255,255,255,0.55) !important; letter-spacing: 0.5px; }

.progress-tracker { background: rgba(0,0,0,0.2); border-radius: 12px; padding: 14px 16px; margin: 10px 0; }
.progress-item { display: flex; align-items: center; gap: 10px; padding: 5px 0; font-size: 12px; color: rgba(255,255,255,0.6) !important; }
.progress-item.done { color: #7FE5A0 !important; }
.progress-dot { width: 8px; height: 8px; border-radius: 50%; background: rgba(255,255,255,0.25); flex-shrink: 0; }
.progress-dot.done { background: #27AE60; }

.sidebar-metric { background: rgba(255,255,255,0.08); border-radius: 10px; padding: 10px 14px; margin: 5px 0; display: flex; justify-content: space-between; align-items: center; }
.sidebar-metric-label { font-size: 12px !important; color: rgba(255,255,255,0.6) !important; }
.sidebar-metric-value { font-size: 16px !important; font-weight: 700 !important; color: white !important; }

.card {
    background: white !important; border-radius: 12px; padding: 18px 22px;
    margin-bottom: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    border-left: 4px solid #2E86AB; color: #2C3E50 !important;
}
.question-card {
    background: white !important; border-radius: 12px; padding: 16px 20px;
    margin-bottom: 10px; box-shadow: 0 1px 6px rgba(0,0,0,0.06);
    border-left: 4px solid #2E86AB; color: #2C3E50 !important;
}
.bullet-card-old {
    background: #FFF5F2 !important; border-radius: 12px; padding: 16px 20px;
    margin-bottom: 10px; border-left: 4px solid #E74C3C; color: #2C3E50 !important; height: 100%;
}
.bullet-card-new {
    background: #F0FDF4 !important; border-radius: 12px; padding: 16px 20px;
    margin-bottom: 10px; border-left: 4px solid #27AE60; color: #2C3E50 !important; height: 100%;
}
.cover-letter-box {
    background: white !important; border-radius: 12px; padding: 30px 36px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08); border: 1px solid #E0E6ED;
    color: #2C3E50 !important; font-size: 15px; line-height: 1.8; white-space: pre-wrap;
}

.chip-blue { display: inline-block; background: #2E86AB; color: white !important; border-radius: 20px; padding: 4px 14px; margin: 3px; font-size: 13px; font-weight: 600; }
.chip-green { display: inline-block; background: #27AE60; color: white !important; border-radius: 20px; padding: 4px 14px; margin: 3px; font-size: 13px; font-weight: 600; }
.chip-red { display: inline-block; background: #E74C3C; color: white !important; border-radius: 20px; padding: 4px 14px; margin: 3px; font-size: 13px; font-weight: 600; }

.badge { display: inline-block; border-radius: 6px; padding: 3px 10px; font-size: 11px; font-weight: 700; color: white !important; margin-right: 8px; }
.badge-tech  { background: #2E86AB; }
.badge-proj  { background: #8E44AD; }
.badge-behav { background: #27AE60; }
.badge-sit   { background: #E67E22; }
.badge-err   { background: #E74C3C; }

.section-title { font-size: 17px; font-weight: 700; color: #1E3A5F !important; margin-top: 24px; margin-bottom: 10px; border-bottom: 2px solid #2E86AB; padding-bottom: 5px; }

[data-testid="stMetricValue"], [data-testid="stMetricLabel"],
[data-testid="stMetricValue"] *, [data-testid="stMetricLabel"] * { color: #1E3A5F !important; }
[data-testid="stAlert"] p, [data-testid="stAlert"] * { color: inherit !important; }
[data-testid="stTabContent"] { overflow: visible !important; }
[data-testid="stTabs"] button { color: #1E3A5F !important; font-weight: 600; font-family: 'Inter', sans-serif !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color: #2E86AB !important; border-bottom-color: #2E86AB !important; }
[data-testid="stTabs"] button p { color: inherit !important; }

.main textarea, .main input { background-color: white !important; color: #2C3E50 !important; font-family: 'Inter', sans-serif !important; border-radius: 10px !important; }
[data-testid="stFileUploaderDropzone"] { background-color: white !important; }
[data-testid="stFileUploaderDropzone"] *:not(svg):not(path) { color: #2C3E50 !important; }
[data-testid="stWidgetLabel"] p, .main label { color: #2C3E50 !important; }

.stButton button[kind="primary"] {
    background: linear-gradient(135deg, #1E3A5F, #2E86AB) !important;
    border: none !important; border-radius: 10px !important;
    font-weight: 600 !important; font-size: 15px !important;
    padding: 12px 24px !important; color: white !important; transition: all 0.2s !important;
}
.stButton button[kind="primary"]:hover {
    opacity: 0.92 !important; transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(30,58,95,0.35) !important;
}

@media screen and (max-width: 768px) {
    .main .block-container { padding-left: 1rem !important; padding-right: 1rem !important; padding-top: 1rem !important; }
    .hero-container { padding: 28px 20px !important; border-radius: 14px !important; margin-bottom: 20px !important; }
    .hero-title { font-size: 26px !important; line-height: 1.3 !important; }
    .hero-title span { font-size: 18px !important; }
    .hero-subtitle { font-size: 14px !important; max-width: 100% !important; }
    .hero-badge { font-size: 11px !important; padding: 4px 10px !important; margin-bottom: 6px !important; }
    .features-row { grid-template-columns: repeat(2, 1fr) !important; gap: 10px !important; }
    .feature-card { padding: 14px 10px !important; }
    .feature-icon { font-size: 22px !important; }
    .feature-title { font-size: 12px !important; }
    .feature-desc { font-size: 10px !important; }
    .steps-row { flex-direction: column !important; align-items: flex-start !important; padding: 16px 18px !important; gap: 14px !important; }
    .step-item { width: 100% !important; }
    .step-arrow { display: none !important; }
    .card, .question-card, .bullet-card-old, .bullet-card-new { padding: 14px 16px !important; }
    .cover-letter-box { padding: 18px 20px !important; font-size: 13px !important; }
    .section-title { font-size: 15px !important; margin-top: 16px !important; }
    .chip-blue, .chip-green, .chip-red { font-size: 11px !important; padding: 3px 10px !important; }
    .badge { font-size: 10px !important; padding: 2px 7px !important; }
    .sidebar-logo-icon { font-size: 28px !important; }
    .sidebar-logo-text { font-size: 15px !important; }
    .sidebar-logo-sub { font-size: 9px !important; }
    .sidebar-metric { padding: 8px 10px !important; }
    .sidebar-metric-value { font-size: 13px !important; }
    .js-plotly-plot { max-width: 100% !important; }
    [data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; min-width: 100% !important; }
    [data-testid="stTabs"] { overflow-x: auto !important; }
    [data-testid="stTabs"] button { font-size: 12px !important; padding: 8px 10px !important; white-space: nowrap !important; }
    .stButton button[kind="primary"] { font-size: 13px !important; padding: 10px 16px !important; }
    [data-testid="stMetricValue"] { font-size: 18px !important; }
    [data-testid="stMetricLabel"] { font-size: 11px !important; }
    .main textarea { font-size: 13px !important; }
}

@media screen and (max-width: 480px) {
    .hero-title { font-size: 22px !important; }
    .features-row { grid-template-columns: 1fr !important; }
    .hero-badge { display: block !important; width: fit-content !important; margin-bottom: 8px !important; }
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════
for key in ["parsed_data", "score_data", "resume_text", "last_file",
            "jd_match", "interview_qs", "jd_text_cache", "pdf_bytes",
            "bullet_rewrites", "cover_letter"]:
    if key not in st.session_state:
        st.session_state[key] = None

if "analyzing" not in st.session_state:
    st.session_state["analyzing"] = False


# ═══════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════
def make_gauge(score: int, title: str = "ATS Score", suffix: str = "/100"):
    score = int(score or 0)
    if score >= 70:
        colour, label = "#27AE60", "Excellent"
    elif score >= 45:
        colour, label = "#E67E22", "Fair"
    else:
        colour, label = "#E74C3C", "Needs Work"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": suffix, "font": {"size": 36, "color": colour, "family": "Inter"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#B0BEC5", "tickfont": {"size": 11}},
            "bar":  {"color": colour, "thickness": 0.3},
            "bgcolor": "white", "borderwidth": 0,
            "steps": [
                {"range": [0,  45], "color": "#FDECEA"},
                {"range": [45, 70], "color": "#FFF8E1"},
                {"range": [70, 100], "color": "#E8F5E9"},
            ],
            "threshold": {"line": {"color": colour, "width": 4}, "thickness": 0.78, "value": score},
        },
        title={
            "text": f"{title}<br><span style='font-size:13px;color:{colour}'>{label}</span>",
            "font": {"size": 17, "color": "#1E3A5F"}
        },
    ))
    fig.update_layout(
        height=270, margin=dict(t=50, b=10, l=30, r=30),
        paper_bgcolor="white", font={"color": "#2C3E50", "family": "Inter"}
    )
    return fig


def section(title: str):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


def chips(keywords: list, colour: str = "blue") -> str:
    return " ".join(f'<span class="chip-{colour}">{k}</span>' for k in keywords)


def badge_html(qtype: str) -> str:
    cls = {
        "Technical": "badge-tech",
        "Project-Based": "badge-proj",
        "Behavioral": "badge-behav",
        "Situational": "badge-sit"
    }.get(qtype, "badge-err")
    return f'<span class="badge {cls}">{qtype}</span>'


def quota_guard(text: str):
    if "QUOTA_EXCEEDED" in str(text) or "quota" in str(text).lower():
        st.error(
            "⚠️ **Gemini API Quota Exceeded**\n\n"
            "You've hit the free-tier limit of **20 requests/day**.\n\n"
            "- ⏳ Wait 24 hours for the quota to reset\n"
            "- 💳 Upgrade at https://ai.dev/rate-limit\n"
            "- 🔄 Switch to `gemini-1.5-flash` in `gemini_helper_new.py`"
        )
        st.stop()


# ═══════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <span class="sidebar-logo-icon">📄</span>
        <div class="sidebar-logo-text">SmartResume AI</div>
        <div class="sidebar-logo-sub">AI-POWERED CAREER TOOLKIT</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    page = st.radio(
        "Navigate",
        ["🏠  Home", "🎯  JD Matcher", "🎤  Interview Prep",
         "✏️  Bullet Rewriter", "✉️  Cover Letter", "📥  Download Report"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    has_resume = bool(st.session_state["resume_text"])
    has_score  = bool(st.session_state["score_data"])
    has_jd     = bool(st.session_state["jd_match"])
    has_qs     = bool(st.session_state["interview_qs"])
    has_letter = bool(st.session_state["cover_letter"])

    def prog_item(label, done):
        dot_cls  = "done" if done else ""
        item_cls = "done" if done else ""
        tick     = "✓" if done else "○"
        return f'<div class="progress-item {item_cls}"><span class="progress-dot {dot_cls}"></span>{tick} {label}</div>'

    st.markdown(f"""
    <div class="progress-tracker">
        {prog_item("Resume uploaded", has_resume)}
        {prog_item("ATS score analyzed", has_score)}
        {prog_item("JD matched", has_jd)}
        {prog_item("Interview questions", has_qs)}
        {prog_item("Cover letter", has_letter)}
    </div>
    """, unsafe_allow_html=True)

    if has_score:
        score  = int(st.session_state["score_data"].get("score", 0) or 0)
        colour = "#27AE60" if score >= 70 else ("#E67E22" if score >= 45 else "#E74C3C")
        st.markdown(f"""
        <div class="sidebar-metric">
            <span class="sidebar-metric-label">ATS Score</span>
            <span class="sidebar-metric-value" style="color:{colour} !important">{score}/100</span>
        </div>""", unsafe_allow_html=True)

    if has_jd:
        ms = int(st.session_state["jd_match"].get("match_score", 0) or 0)
        mc = "#27AE60" if ms >= 70 else ("#E67E22" if ms >= 45 else "#E74C3C")
        st.markdown(f"""
        <div class="sidebar-metric">
            <span class="sidebar-metric-label">JD Match</span>
            <span class="sidebar-metric-value" style="color:{mc} !important">{ms}%</span>
        </div>""", unsafe_allow_html=True)

    if has_qs:
        st.markdown(f"""
        <div class="sidebar-metric">
            <span class="sidebar-metric-label">Interview Questions</span>
            <span class="sidebar-metric-value">{len(st.session_state["interview_qs"])} ready</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        "<div style='font-size:11px;color:rgba(255,255,255,0.4);text-align:center'>"
        "Powered by Gemini 2.5 Flash<br>Built with Streamlit + Plotly</div>",
        unsafe_allow_html=True
    )


# ═══════════════════════════════════════════════════
# PAGE 1 — HOME
# ═══════════════════════════════════════════════════
if page == "🏠  Home":

    st.markdown("""
    <div class="hero-container">
        <div class="hero-title">SmartResume AI<br><span style="font-size:32px;font-weight:600;opacity:0.9">Supercharged by AI</span></div>
        <div class="hero-subtitle">
            Upload your resume and get instant ATS scoring, job description matching,
            interview prep, and a polished cover letter — all in one place.
        </div>
        <span class="hero-badge">⚡ Instant Analysis</span>
        <span class="hero-badge">🎯 ATS Optimized</span>
        <span class="hero-badge">🤖 Powered by Gemini</span>
        <span class="hero-badge">📥 PDF Report</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="features-row">
        <div class="feature-card">
            <span class="feature-icon">📊</span>
            <div class="feature-title">ATS Score</div>
            <div class="feature-desc">Know exactly how your resume ranks with recruiters</div>
        </div>
        <div class="feature-card">
            <span class="feature-icon">🎯</span>
            <div class="feature-title">JD Matcher</div>
            <div class="feature-desc">See keyword gaps vs any job description instantly</div>
        </div>
        <div class="feature-card">
            <span class="feature-icon">🎤</span>
            <div class="feature-title">Interview Prep</div>
            <div class="feature-desc">10 targeted questions based on your real resume</div>
        </div>
        <div class="feature-card">
            <span class="feature-icon">✏️</span>
            <div class="feature-title">Bullet Rewriter</div>
            <div class="feature-desc">Turn weak bullets into impact-driven statements</div>
        </div>
        <div class="feature-card">
            <span class="feature-icon">✉️</span>
            <div class="feature-title">Cover Letter</div>
            <div class="feature-desc">AI-written, tailored to your resume and the role</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="steps-row">
        <div class="step-item">
            <div class="step-number">1</div>
            <div>
                <div class="step-text-title">Upload Resume</div>
                <div class="step-text-sub">PDF format, any layout</div>
            </div>
        </div>
        <span class="step-arrow">›</span>
        <div class="step-item">
            <div class="step-number">2</div>
            <div>
                <div class="step-text-title">Analyze</div>
                <div class="step-text-sub">AI parses & scores in seconds</div>
            </div>
        </div>
        <span class="step-arrow">›</span>
        <div class="step-item">
            <div class="step-number">3</div>
            <div>
                <div class="step-text-title">Match JD</div>
                <div class="step-text-sub">Paste any job description</div>
            </div>
        </div>
        <span class="step-arrow">›</span>
        <div class="step-item">
            <div class="step-number">4</div>
            <div>
                <div class="step-text-title">Prepare</div>
                <div class="step-text-sub">Interview questions + cover letter</div>
            </div>
        </div>
        <span class="step-arrow">›</span>
        <div class="step-item">
            <div class="step-number">5</div>
            <div>
                <div class="step-text-title">Download</div>
                <div class="step-text-sub">Full PDF report to share</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="upload-label">📂 Upload Your Resume</div>
    <div class="upload-hint">Supports PDF format · Your file is processed locally and never stored</div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload Resume", type=["pdf"], label_visibility="collapsed")

    if uploaded_file is not None:
        if st.session_state["last_file"] != uploaded_file.name:
            st.session_state["resume_text"]     = extract_text(uploaded_file)
            st.session_state["last_file"]        = uploaded_file.name
            st.session_state["parsed_data"]      = None
            st.session_state["score_data"]       = None
            st.session_state["jd_match"]         = None
            st.session_state["interview_qs"]     = None
            st.session_state["jd_text_cache"]    = None
            st.session_state["bullet_rewrites"]  = None
            st.session_state["cover_letter"]     = None
            st.session_state["pdf_bytes"]        = None
            st.session_state["analyzing"]        = False

        st.success(f"✅ **{uploaded_file.name}** uploaded successfully!")

        with st.expander("📃 View Extracted Resume Text", expanded=False):
            st.text_area("Resume Text", st.session_state["resume_text"],
                         height=280, label_visibility="collapsed")

        if not st.session_state.get("analyzing"):
            if st.button("🔍  Analyze Resume", use_container_width=True, type="primary"):
                st.session_state["analyzing"] = True
                st.rerun()
        else:
            with st.spinner("Analyzing your resume… (1 API call)"):
                parsed, score_data = parse_resume_and_score(
                    st.session_state["resume_text"]
                )
                st.session_state["parsed_data"] = parsed
                st.session_state["score_data"]  = score_data
                st.session_state["analyzing"]   = False
            st.rerun()

    if st.session_state["score_data"] is not None:
        data       = st.session_state["parsed_data"]
        score_data = st.session_state["score_data"]
        score      = int(score_data.get("score", 0) or 0)

        for w in score_data.get("weaknesses", []):
            quota_guard(str(w))

        st.divider()

        tab_score, tab_info, tab_skills, tab_edu, tab_exp, tab_proj, tab_cert = st.tabs([
            "📊 Score", "👤 Info", "🛠 Skills",
            "🎓 Education", "💼 Experience", "🚀 Projects", "📜 Certs & More"
        ])

        with tab_score:
            col_g, col_v = st.columns([1, 1], gap="large")
            with col_g:
                st.plotly_chart(make_gauge(score), use_container_width=True)
            with col_v:
                st.markdown("#### 📝 Verdict")
                st.markdown(
                    f'<div class="card">{score_data.get("verdict", "No verdict available.")}</div>',
                    unsafe_allow_html=True
                )
                st.progress(score / 100, text=f"ATS Score: {score}/100")
            col_s, col_w = st.columns(2, gap="medium")
            with col_s:
                section("✅ Strengths")
                for item in score_data.get("strengths", []):
                    st.success(item)
            with col_w:
                section("⚠️ Areas for Improvement")
                for item in score_data.get("weaknesses", []):
                    st.warning(item)

        with tab_info:
            section("👤 Candidate Information")
            c1, c2, c3 = st.columns(3)
            c1.metric("Name",  data.get("name",  "Not Found"))
            c2.metric("Email", data.get("email", "Not Found"))
            c3.metric("Phone", data.get("phone", "Not Found"))

        with tab_skills:
            section("🛠 Skills")
            skills = data.get("skills", [])
            if skills:
                st.markdown(chips(skills, "blue"), unsafe_allow_html=True)
            else:
                st.info("No skills found.")

        with tab_edu:
            section("🎓 Education")
            for edu in data.get("education", []):
                if isinstance(edu, dict):
                    st.markdown(
                        f"**{edu.get('degree', '')}**  \n"
                        f"🏫 {edu.get('institution', '')}  \n"
                        f"📅 {edu.get('date', '')}"
                    )
                    st.divider()

        with tab_exp:
            section("💼 Experience")
            experience = data.get("experience", [])
            if experience:
                for exp in experience:
                    if isinstance(exp, dict):
                        st.markdown(
                            f"**{exp.get('role', '')}**  \n"
                            f"🏢 {exp.get('company', '')}  \n"
                            f"📅 {exp.get('duration', '')}  \n"
                            f"{exp.get('description', '')}"
                        )
                        st.divider()
            else:
                st.info("No experience found.")

        with tab_proj:
            section("🚀 Projects")
            projects = data.get("projects", [])
            if projects:
                for p in projects:
                    if isinstance(p, dict):
                        st.markdown(
                            f"**{p.get('title', '')}**  \n"
                            f"{p.get('description', '')}"
                        )
                        st.divider()
            else:
                st.info("No projects found.")

        with tab_cert:
            section("📜 Certifications")
            certs = data.get("certifications", [])
            if certs:
                for cert in certs:
                    if isinstance(cert, dict):
                        st.markdown(
                            f"**{cert.get('name', '')}**  \n"
                            f"🏢 {cert.get('issuer', '')}  \n"
                            f"📅 {cert.get('date', '')}"
                        )
                        st.divider()
                    else:
                        st.write(f"• {cert}")
            else:
                st.info("No certifications found.")

            section("🏆 Achievements")
            for ach in data.get("achievements", []):
                st.success(ach)


# ═══════════════════════════════════════════════════
# PAGE 2 — JD MATCHER
# ═══════════════════════════════════════════════════
elif page == "🎯  JD Matcher":
    st.title("🎯 Job Description Matcher")
    st.markdown("Paste a job description to see how well your resume matches it.")
    st.divider()

    if not st.session_state.get("resume_text"):
        st.warning("⚠️ Please upload and analyze your resume first on the **🏠 Home** page.")
        st.stop()

    jd_text = st.text_area(
        "Paste Job Description here",
        height=220,
        placeholder="e.g. We are looking for a Python developer with experience in Machine Learning, TensorFlow, NLP…"
    )

    if st.button("🎯  Match Resume to JD", use_container_width=True, type="primary"):
        if not jd_text.strip():
            st.error("Please paste a job description first.")
        else:
            with st.spinner("Matching resume to JD… (1 API call)"):
                result = match_jd(st.session_state["resume_text"], jd_text)
                st.session_state["jd_match"]      = result
                st.session_state["jd_text_cache"] = jd_text
            st.rerun()

    if st.session_state.get("jd_match"):
        m  = st.session_state["jd_match"]
        ms = int(m.get("match_score", 0) or 0)
        quota_guard(str(m.get("match_verdict", "")))

        col_g, col_v = st.columns([1, 1], gap="large")
        with col_g:
            mc = "#27AE60" if ms >= 70 else ("#E67E22" if ms >= 45 else "#E74C3C")
            ml = "Strong Match" if ms >= 70 else ("Partial Match" if ms >= 45 else "Weak Match")
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=ms,
                number={"suffix": "%", "font": {"size": 36, "color": mc, "family": "Inter"}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#B0BEC5"},
                    "bar":  {"color": mc, "thickness": 0.3},
                    "bgcolor": "white", "borderwidth": 0,
                    "steps": [
                        {"range": [0,  45], "color": "#FDECEA"},
                        {"range": [45, 70], "color": "#FFF8E1"},
                        {"range": [70, 100], "color": "#E8F5E9"},
                    ],
                    "threshold": {"line": {"color": mc, "width": 4}, "thickness": 0.78, "value": ms},
                },
                title={
                    "text": f"JD Match Score<br><span style='font-size:13px;color:{mc}'>{ml}</span>",
                    "font": {"size": 17, "color": "#1E3A5F"}
                },
            ))
            fig.update_layout(height=270, margin=dict(t=50, b=10, l=30, r=30), paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)
        with col_v:
            st.markdown("#### 📝 Match Verdict")
            st.markdown(
                f'<div class="card">{m.get("match_verdict", "")}</div>',
                unsafe_allow_html=True
            )
            st.progress(ms / 100, text=f"Match Score: {ms}%")

        st.divider()
        col_match, col_miss, col_rec = st.columns(3, gap="medium")
        with col_match:
            section("✅ Matched Keywords")
            matched = m.get("matched_keywords", [])
            st.markdown(chips(matched, "green") if matched else "_None found._", unsafe_allow_html=True)
        with col_miss:
            section("❌ Missing Keywords")
            missing = m.get("missing_keywords", [])
            st.markdown(chips(missing, "red") if missing else "_None missing — great match!_", unsafe_allow_html=True)
        with col_rec:
            section("💡 Recommended to Add")
            rec = m.get("recommended_keywords", [])
            st.markdown(chips(rec, "blue") if rec else "_No additional recommendations._", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
# PAGE 3 — INTERVIEW PREP
# ═══════════════════════════════════════════════════
elif page == "🎤  Interview Prep":
    st.title("🎤 Interview Question Generator")
    st.markdown("Get 10 targeted interview questions based on your resume and role.")
    st.divider()

    if not st.session_state.get("resume_text"):
        st.warning("⚠️ Please upload and analyze your resume first on the **🏠 Home** page.")
        st.stop()

    prefill  = st.session_state.get("jd_text_cache") or ""
    jd_input = st.text_area(
        "Paste Job Description for targeted questions (optional)",
        value=prefill,
        height=150,
        placeholder="Leave blank for general questions based only on your resume…"
    )

    if st.button("🎤  Generate Interview Questions", use_container_width=True, type="primary"):
        with st.spinner("Generating questions… (1 API call)"):
            qs = generate_interview_questions(st.session_state["resume_text"], jd_input)
            st.session_state["interview_qs"] = qs
        st.rerun()

    if st.session_state.get("interview_qs"):
        qs = st.session_state["interview_qs"]
        if qs and "QUOTA_EXCEEDED" in str(qs[0].get("question", "")):
            quota_guard("QUOTA_EXCEEDED")

        type_counts = {}
        for q in qs:
            t = q.get("type", "General")
            type_counts[t] = type_counts.get(t, 0) + 1

        st.markdown(f"### {len(qs)} Questions Generated")
        cols = st.columns(len(type_counts))
        for i, (qtype, count) in enumerate(type_counts.items()):
            cols[i].metric(qtype, count)
        st.divider()

        for q in qs:
            st.markdown(
                f'<div class="question-card">{badge_html(q.get("type", "General"))}'
                f'<strong>Q{q.get("number", "")}.</strong> {q.get("question", "")}</div>',
                unsafe_allow_html=True
            )


# ═══════════════════════════════════════════════════
# PAGE 4 — BULLET REWRITER
# ═══════════════════════════════════════════════════
elif page == "✏️  Bullet Rewriter":
    st.title("✏️ Resume Bullet Rewriter")
    st.markdown("Paste weak resume bullets and get AI-powered, impact-driven rewrites.")
    st.divider()

    bullets_input = st.text_area(
        "Paste your resume bullets (one per line)",
        height=180,
        placeholder="Created an AI project.\nWorked on a team to build a website.\nDid data analysis for college project."
    )

    if st.button("✨  Rewrite Bullets", use_container_width=True, type="primary"):
        if not bullets_input.strip():
            st.error("Please enter at least one bullet point.")
        else:
            with st.spinner("Rewriting bullets… (1 API call)"):
                rewrites = rewrite_bullets(bullets_input)
                st.session_state["bullet_rewrites"] = rewrites
            st.rerun()

    if st.session_state.get("bullet_rewrites"):
        rewrites = st.session_state["bullet_rewrites"]
        if rewrites and "QUOTA_EXCEEDED" in str(rewrites[0].get("improved", "")):
            quota_guard("QUOTA_EXCEEDED")
        st.divider()
        st.markdown(f"### {len(rewrites)} Bullets Improved")
        for rw in rewrites:
            col_old, col_new = st.columns(2, gap="medium")
            with col_old:
                st.markdown(
                    f'<div class="bullet-card-old"><b>❌ Original</b><br><br>{rw.get("original", "")}</div>',
                    unsafe_allow_html=True
                )
            with col_new:
                st.markdown(
                    f'<div class="bullet-card-new"><b>✅ Improved</b><br><br>{rw.get("improved", "")}</div>',
                    unsafe_allow_html=True
                )
            st.markdown("")


# ═══════════════════════════════════════════════════
# PAGE 5 — COVER LETTER
# ═══════════════════════════════════════════════════
elif page == "✉️  Cover Letter":
    st.title("✉️ Cover Letter Generator")
    st.markdown("Generate a tailored cover letter using your resume and a job description.")
    st.divider()

    if not st.session_state.get("resume_text"):
        st.warning("⚠️ Please upload and analyze your resume first on the **🏠 Home** page.")
        st.stop()

    col_company, col_role = st.columns(2)
    with col_company:
        company_name = st.text_input("Company Name (optional)", placeholder="e.g. Google")
    with col_role:
        role_title = st.text_input("Role Title (optional)", placeholder="e.g. Software Engineer Intern")

    tone = st.selectbox(
        "Tone",
        ["Professional", "Enthusiastic", "Confident", "Formal", "Conversational"]
    )

    prefill_jd = st.session_state.get("jd_text_cache") or ""
    jd_text    = st.text_area(
        "Paste Job Description",
        value=prefill_jd,
        height=200,
        placeholder="Paste the job description you're applying to…"
    )

    if st.button("✉️  Generate Cover Letter", use_container_width=True, type="primary"):
        if not jd_text.strip():
            st.error("Please paste a job description first.")
        else:
            with st.spinner("Writing your cover letter… (1 API call)"):
                result = generate_cover_letter(
                    resume_text=st.session_state["resume_text"],
                    jd_text=jd_text,
                    tone=tone,
                    company_name=company_name,
                    role_title=role_title
                )
                st.session_state["cover_letter"] = result.get("cover_letter", "")
            st.rerun()

    if st.session_state.get("cover_letter"):
        letter = st.session_state["cover_letter"]
        quota_guard(letter)
        st.divider()
        section("✉️ Your Cover Letter")
        st.markdown(f'<div class="cover-letter-box">{letter}</div>', unsafe_allow_html=True)
        st.download_button(
            label="⬇️ Download as Text File",
            data=letter,
            file_name="Cover_Letter.txt",
            mime="text/plain",
            use_container_width=True
        )


# ═══════════════════════════════════════════════════
# PAGE 6 — DOWNLOAD REPORT
# ═══════════════════════════════════════════════════
elif page == "📥  Download Report":
    st.title("📥 Download Analysis Report")
    st.markdown("Generate a polished PDF with everything you've analyzed so far.")
    st.divider()

    if not st.session_state.get("score_data"):
        st.warning("⚠️ Please analyze your resume first on the **🏠 Home** page.")
        st.stop()

    candidate_name = (st.session_state.get("parsed_data") or {}).get("name", "Candidate")

    section("📋 Report Contents")
    st.markdown(f"- ✅ ATS Score, Strengths & Weaknesses for **{candidate_name}**")
    if st.session_state.get("jd_match"):
        st.markdown("- ✅ JD Match Score & Keywords")
    else:
        st.markdown("- ⬜ JD Match — _not done yet (optional, visit 🎯 JD Matcher)_")
    if st.session_state.get("interview_qs"):
        st.markdown(f"- ✅ {len(st.session_state['interview_qs'])} Interview Questions")
    else:
        st.markdown("- ⬜ Interview Questions — _not done yet (optional, visit 🎤 Interview Prep)_")

    st.divider()

    if st.button("📄  Generate PDF Report", use_container_width=True, type="primary"):
        with st.spinner("Generating PDF…"):
            pdf_bytes = generate_pdf_report(
                candidate_name=candidate_name,
                score_data=st.session_state["score_data"],
                jd_match=st.session_state.get("jd_match"),
                interview_questions=st.session_state.get("interview_qs"),
            )
        st.session_state["pdf_bytes"] = pdf_bytes
        st.success("✅ Report ready!")

    if st.session_state.get("pdf_bytes"):
        safe_name = candidate_name.replace(" ", "_") or "Candidate"
        st.download_button(
            label="⬇️ Download Report PDF",
            data=st.session_state["pdf_bytes"],
            file_name=f"SmartResume_Report_{safe_name}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )